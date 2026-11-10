# AWS IoT Core & Amazon SNS Email Notification Setup Guide

This guide walks you through setting up the serverless cloud backend to receive telemetry from the M5Stamp ESP32-S3 and trigger email alerts upon fire/gas anomalies.

---

### Step 1: Create Amazon SNS Topic & Email Subscription
1. Log in to the [AWS Management Console](https://aws.amazon.com/console).
2. Navigate to **Amazon SNS (Simple Notification Service)**.
3. Click **Topics** $\rightarrow$ **Create topic**.
   - Type: **Standard**
   - Name: `FireAndGasAlerts`
   - Click **Create topic**.
4. In the topic details page, click **Create subscription**:
   - Protocol: `Email`
   - Endpoint: `your_email@university.edu` (Enter your email address)
   - Click **Create subscription**.
5. **Check your email inbox**: Open the email from AWS Notifications and click **"Confirm subscription"**.

---

### Step 2: Create Amazon DynamoDB Table
1. Open **Amazon DynamoDB** $\rightarrow$ **Tables** $\rightarrow$ **Create table**.
   - Table name: `M5Stack_Telemetry`
   - Partition key (Hash): `device_id` (String)
   - Sort key (Range): `received_at` (Number)
   - Table settings: **Customized settings** $\rightarrow$ Capacity mode: **On-demand** (Zero idle cost).
   - Click **Create table**.

---

### Step 3: Create AWS IoT Core Routing Rule
1. Open **AWS IoT Core** $\rightarrow$ **Message Routing** $\rightarrow$ **Rules** $\rightarrow$ **Create rule**.
2. Rule name: `M5Stamp_Fire_Alert_Rule`
3. SQL statement:
   ```sql
   SELECT * FROM 'sensors/m5stamp/telemetry'
   ```
4. Attach **Action 1 (DynamoDB Insert)**:
   - Select **DynamoDBv2**.
   - Table name: `M5Stack_Telemetry`.
   - IAM Role: Click **Create new role** (`M5Stamp_IoT_DynamoDB_Role`).
5. Attach **Action 2 (SNS Email Alert)**:
   - Click **Add another action** $\rightarrow$ **Simple Notification Service (SNS)**.
   - Select SNS Topic: `FireAndGasAlerts`.
   - Message format: `RAW`.
   - Under SQL statement condition, add:
     ```sql
     WHERE fire_alert = true OR temperature_c > 50.0 OR gas_resistance_kohm < 12.0
     ```
6. Click **Create rule**.

Now, whenever the M5Stamp detects a fire or gas hazard and powers up its Wi-Fi, AWS will log the telemetry to DynamoDB and immediately dispatch an urgent email to your inbox!
