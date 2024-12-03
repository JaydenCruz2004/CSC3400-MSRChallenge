import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from dateutil.parser import parse
import re
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import mean_absolute_error, mean_squared_error, root_mean_squared_error

def load_data(directory):
    """Load JSON files from the specified directory."""
    data_list = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r") as file:
                    data = json.load(file)
                    if isinstance(data, list):  # Ensure it's a list of dictionaries
                        data_list.extend(data)
                    elif isinstance(data, dict):
                        data_list.append(data)
                    else:
                        print(f"Skipping invalid JSON structure in {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return data_list



def convert_to_datetime(date_str):
    """Convert a string to offset-naive datetime or return None for invalid formats."""
    try:
        # Parse the date string and strip timezone info
        dt = parse(date_str, fuzzy=True)
        return dt.replace(tzinfo=None)
    except ValueError:
        pass

    # Handle common patterns
    if re.match(r'^\d+(\.\d+)+(\.Final)?$', date_str):
        print(f"Unrecognized date format (likely a version): {date_str}. Skipping.")
        return None

    if re.match(r'^\d+\.\d+\.\d+\.\w+\d+$', date_str):
        print(f"Date format with version suffix: {date_str}. Skipping.")
        return None

    if re.match(r'^\d+\.\d+\.\d+-rc-\d+$', date_str):
        print(f"Date format with release candidate: {date_str}. Skipping.")
        return None

    print(f"Unrecognized date format: {date_str}. Skipping.")
    return None


def log_skipped_entries(entry_id, reason, log_file="skipped_entries.log"):
    """Log skipped entries with the reason."""
    with open(log_file, "a") as file:
        file.write(f"Entry ID: {entry_id}, Reason: {reason}\n")


def extract_patch_times(data_list, log_file="skipped_entries.log"):
    """Extract patch times and features from data."""
    patch_times = []
    features = []
    for entry in data_list:
        entry_id = entry.get('id', 'Unknown')
        try:
            published_date = convert_to_datetime(entry.get("published"))
            if not published_date:
                log_skipped_entries(entry_id, "Invalid or missing published date", log_file)
                continue

            fixed_dates = []
            for item in entry.get("affected", []):
                for range_info in item.get("ranges", []):
                    if "events" in range_info:
                        for event in range_info["events"]:
                            if "fixed" in event:
                                date = convert_to_datetime(event["fixed"])
                                if date:
                                    fixed_dates.append(date)

            if not fixed_dates:
                log_skipped_entries(entry_id, "No valid fixed dates", log_file)
                continue

            fixed_date = min(fixed_dates)
            if fixed_date <= published_date:
                log_skipped_entries(entry_id, f"Fixed date ({fixed_date}) before published date ({published_date})", log_file)
                continue

            patch_time = (fixed_date - published_date).total_seconds() / (60 * 60)
            patch_times.append(patch_time)

            severity_score = 0
            for severity_info in entry.get("severity", []):
                if severity_info["type"] == "CVSS_V3":
                    try:
                        severity_score = float(severity_info["score"].split("/")[1].split(":")[1])
                    except (IndexError, ValueError):
                        severity_score = np.nan
                        log_skipped_entries(entry_id, "Invalid severity score", log_file)

            versions_length = sum(len(item.get("versions", [])) for item in entry.get("affected", []))
            features.append([severity_score if not np.isnan(severity_score) else 0, versions_length])

        except Exception as e:
            log_skipped_entries(entry_id, f"Processing error: {e}", log_file)
            continue

    # Handle missing values in patch times
    patch_times = pd.Series(patch_times).interpolate().tolist()
    return np.array(features), np.array(patch_times)


def create_sequences(data, target, sequence_length):
    """Create sequences for LSTM input."""
    if len(data) < sequence_length:
        print(f"Not enough data to form sequences. Adjusting sequence length to {len(data)}.")
        sequence_length = len(data)

    sequences = []
    targets = []
    for i in range(len(data) - sequence_length):
        seq = data[i:i + sequence_length]
        label = target[i + sequence_length]
        sequences.append(seq)
        targets.append(label)
    return np.array(sequences), np.array(targets)


def build_lstm_model(input_shape):
    """Build and compile an LSTM model."""
    model = Sequential([
        tf.keras.Input(shape=input_shape),  # Specify input shape directly
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(1)  # Output layer for regression
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model


def train_and_evaluate(features, patch_times, sequence_length=5, epochs=50, batch_size=16):
    """Train and evaluate an LSTM model or fallback model."""
    if len(patch_times) <= sequence_length:
        print("Not enough data for LSTM. Falling back to simpler model...")
        fallback_model(features, patch_times)
        return

    scaler = MinMaxScaler()
    features_scaled = scaler.fit_transform(features)
    patch_times_scaled = scaler.fit_transform(patch_times.reshape(-1, 1))

    X, y = create_sequences(features_scaled, patch_times_scaled, sequence_length)
    if len(X) == 0:
        print("Insufficient sequences for LSTM. Falling back to simpler model...")
        fallback_model(features, patch_times)
        return

    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epochs, batch_size=batch_size)

    # Evaluate model performance
    # Evaluate model performance
    predictions = model.predict(X_test)
    predictions_rescaled = scaler.inverse_transform(predictions)
    y_test_rescaled = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Calculate evaluation metrics
    mae = mean_absolute_error(y_test_rescaled, predictions_rescaled)
    rmse = root_mean_squared_error(y_test_rescaled, predictions_rescaled)
    print(f"Mean Absolute Error: {mae}")
    print(f"Root Mean Squared Error: {rmse}")

    # Calculate predicted average patch time
    predicted_avg_patch_time = np.mean(predictions_rescaled)
    print(f"Predicted Average Patch Time: {predicted_avg_patch_time:.2f} hours")

    # Plot training and validation loss
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.legend()
    plt.title("Training and Validation Loss")
    plt.show()

    # Plot predictions vs actual values
    plt.figure(figsize=(10, 6))
    plt.plot(y_test_rescaled, label="Actual Patch Times")
    plt.plot(predictions_rescaled, label="Predicted Patch Times", linestyle="dashed")
    plt.legend()
    plt.title("Actual vs Predicted Patch Times")
    plt.show()


def fallback_model(features, patch_times):
    """Use a simpler model (e.g., linear regression) if LSTM is not viable."""
    if len(features) < 2:
        print("Insufficient data for fallback model. Exiting...")
        return

    scaler = MinMaxScaler()
    features_scaled = scaler.fit_transform(features)
    patch_times_scaled = scaler.fit_transform(patch_times.reshape(-1, 1))

    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(features_scaled, patch_times_scaled)

    predictions = model.predict(features_scaled)
    plt.figure(figsize=(10, 6))
    plt.plot(scaler.inverse_transform(patch_times_scaled), label="Actual Patch Times")
    plt.plot(scaler.inverse_transform(predictions), label="Predicted Patch Times", linestyle="dashed")
    plt.legend()
    plt.title("Fallback Model: Linear Regression Results")
    plt.show()

if __name__ == "__main__":
    data_directory = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Kimberly'sFiles2"
    data_list = load_data(data_directory)

    features, patch_times = extract_patch_times(data_list)
    if len(patch_times) > 0:
        avg_patch_time = np.mean(patch_times)
        print(f"Average Patch Time: {avg_patch_time:.2f} hours")
    else:
        print("No valid patch times found.")

    train_and_evaluate(features, patch_times)