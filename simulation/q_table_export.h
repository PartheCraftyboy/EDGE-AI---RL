/*
 * Auto-generated Q-Table for M5Stamp ESP32-S3 Fire & Gas Adaptive Sensing
 * Dimensions: 54 states x 4 actions
 * Actions:
 *   0: DEEP_SLEEP_LONG  (600s, no heater, no wifi)
 *   1: NORMAL_CYCLE     (60s, pulse heater, no wifi)
 *   2: ELEVATED_SCAN    (10s, pulse heater, no wifi)
 *   3: EMERGENCY_ALERT  (2s, full heater, turn on WiFi & Alert AWS)
 */

#ifndef Q_TABLE_EXPORT_H
#define Q_TABLE_EXPORT_H

#define NUM_STATES 54
#define NUM_ACTIONS 4

static const float Q_TABLE[NUM_STATES][NUM_ACTIONS] = {
    /* State 00 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 01 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 02 */ { -61.2552f, 43.9758f, 1.0941f, -74.1299f },
    /* State 03 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 04 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 05 */ { -0.2652f, 24.6831f, 0.1809f, -51.8226f },
    /* State 06 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 07 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 08 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 09 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 10 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 11 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 12 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 13 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 14 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 15 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 16 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 17 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 18 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 19 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 20 */ { -73.8036f, 66.0109f, 0.0000f, 0.0000f },
    /* State 21 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 22 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 23 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 24 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 25 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 26 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 27 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 28 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 29 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 30 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 31 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 32 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 33 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 34 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 35 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 36 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 37 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 38 */ { -560.9579f, 239.9945f, 308.0421f, 401.6566f },
    /* State 39 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 40 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 41 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 42 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 43 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 44 */ { -559.3842f, 237.3953f, 323.8025f, 377.0816f },
    /* State 45 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 46 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 47 */ { -446.2000f, 238.0664f, 218.0935f, 183.1274f },
    /* State 48 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 49 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 50 */ { -573.6046f, 235.7552f, 311.2543f, 343.8562f },
    /* State 51 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 52 */ { 0.0000f, 0.0000f, 0.0000f, 0.0000f },
    /* State 53 */ { -602.2534f, 154.7291f, 221.3491f, 344.4667f },
};

inline int get_rl_action(int state_idx) {
    if (state_idx < 0 || state_idx >= NUM_STATES) return 1; // default NORMAL_CYCLE
    int best_a = 0;
    float max_q = Q_TABLE[state_idx][0];
    for (int a = 1; a < NUM_ACTIONS; a++) {
        if (Q_TABLE[state_idx][a] > max_q) {
            max_q = Q_TABLE[state_idx][a];
            best_a = a;
        }
    }
    return best_a;
}

#endif // Q_TABLE_EXPORT_H
