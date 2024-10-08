// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef ppx_ui_util_h
#define ppx_ui_util_h

#include <cmath>
#include <cstdint>
#include <type_traits>

#include "ppx/log.h"
#include "ppx/timer.h"

namespace ppx {

template <typename FloatT>
struct ParallelVariance
{
    FloatT weight = 0.0;
    FloatT mean   = 0.0;
    FloatT accVar = 0.0;

    FloatT Mean() const { return mean; }
    FloatT PopulationVariance() const { return accVar / weight; }
    FloatT SampleVariance() const { return accVar / (weight - 1.0); }

    static ParallelVariance Combine(const ParallelVariance& a, const ParallelVariance& b)
    {
        // Chan et al. online variance algorithm
        // https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Parallel_algorithm
        //
        // Large weight might cause problem with mean calculation.
        // Since we are doing it for display in UI, that's not a issue.
        const FloatT delta  = b.mean - a.mean;
        const FloatT weight = a.weight + b.weight;
        return {
            weight,
            a.mean + delta * (b.weight / weight),
            a.accVar + b.accVar + (delta * delta) * (a.weight * b.weight / weight),
        };
    }
};

template <typename FloatT>
class MovingAverage
{
public:
    FloatT Mean() const { return mData.Mean(); }
    FloatT Variance() const { return mVariance; }

    // Decay the weight applied to previous variables by multiplier
    void Decay(float multiplier)
    {
        mData = {mData.weight * multiplier, mData.mean, mData.accVar * multiplier};
        // No update to the population variance.
    }

    void Append(FloatT value, FloatT weight = 1.0)
    {
        mData     = ParallelVariance<FloatT>::Combine(mData, {weight, value, 0.0});
        mVariance = mData.PopulationVariance();
    }

private:
    ParallelVariance<FloatT> mData;
    FloatT                   mVariance;
};

// Sequence of value for realtime UI display.
// It keep track of the latest value and a weighted average where w_i = e^{(t_i-t_{now})/halfLife}
// T is the type of value, FloatT is used for collecting statistics.
template <typename T, typename FloatT = std::conditional_t<std::is_floating_point_v<T>, T, float>>
class RealtimeValue
{
public:
    static constexpr FloatT kDefaultHalfLife = 0.5;
    RealtimeValue(FloatT halfLife = kDefaultHalfLife)
        : mHalfLife(halfLife)
    {
    }

    void Update(T value)
    {
        uint64_t timestamp;
        if (Timer::Timestamp(&timestamp) != ppx::TIMER_RESULT_SUCCESS) {
            PPX_LOG_INFO("Failed to get timestamp");
            return;
        };
        const FloatT elapsedNano      = static_cast<FloatT>(timestamp - mTimestamp);
        const FloatT elapsed          = elapsedNano * static_cast<FloatT>(PPX_TIMER_NANOS_TO_SECONDS);
        const FloatT elapsedHalfLifes = elapsed / mHalfLife;

        mMovingAverage.Decay(std::exp2(-elapsedHalfLifes));
        mMovingAverage.Append(static_cast<FloatT>(value));

        mValue     = value;
        mTimestamp = timestamp;
    }

    T      Value() const { return mValue; }
    FloatT Mean() const { return mMovingAverage.Mean(); }
    FloatT Std() const { return std::sqrt(mMovingAverage.Variance()); }

    void ClearHistory() { mMovingAverage.Decay(0); }

private:
    FloatT   mHalfLife;
    T        mValue     = {};
    uint64_t mTimestamp = 0;

    MovingAverage<FloatT> mMovingAverage;
};

} // namespace ppx

#endif // ppx_ui_util_h
