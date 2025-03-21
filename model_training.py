import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle

# Load the combined training dataset
df = pd.read_csv("combined_training_dataset.csv")

# Define features and target variable
# We'll use extracted metadata features for now. Adjust as needed.
features = [
    "query_length", "num_select", "num_from", "num_where",
    "num_join", "num_group_by", "num_order_by", "num_distinct", "num_limit"
]
target = "total_exec_time"

X = df[features]
y = df[target]

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize a model. Let's start with Linear Regression as a baseline.
model_lr = LinearRegression()
model_lr.fit(X_train, y_train)

# Optionally, you can try a more complex model like Random Forest
model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
model_rf.fit(X_train, y_train)

# Predict on test set
y_pred_lr = model_lr.predict(X_test)
y_pred_rf = model_rf.predict(X_test)

# Evaluate models
print("Linear Regression Evaluation:")
print("MAE:", mean_absolute_error(y_test, y_pred_lr))
print("MSE:", mean_squared_error(y_test, y_pred_lr))
print("R2 Score:", r2_score(y_test, y_pred_lr))
print()
print("Random Forest Evaluation:")
print("MAE:", mean_absolute_error(y_test, y_pred_rf))
print("MSE:", mean_squared_error(y_test, y_pred_rf))
print("R2 Score:", r2_score(y_test, y_pred_rf))

# Save the chosen model (for example, the Random Forest model)
with open("sql_cost_predictor.pkl", "wb") as f:
    pickle.dump(model_rf, f)
print("Model saved as sql_cost_predictor.pkl")
