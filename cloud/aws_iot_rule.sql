-- AWS IoT Core SQL Rule
-- Rule Name: M5Stamp_Fire_Alert_And_Telemetry_Rule
-- Topic: sensors/m5stamp/telemetry

SELECT 
    device_id,
    timestamp() AS received_at,
    boot_count,
    fire_alert,
    temperature_c,
    gas_resistance_kohm,
    battery_voltage,
    battery_soc_pct,
    rl_action
FROM 'sensors/m5stamp/telemetry'

-- Action 1: Insert into DynamoDB Table 'M5Stack_Telemetry'
-- Hash Key: device_id
-- Range Key: received_at

-- Action 2 (Conditional): Trigger SNS Topic 'FireAndGasAlerts'
-- WHERE fire_alert = true OR temperature_c > 50.0 OR gas_resistance_kohm < 12.0
