import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
from sklearn.metrics import accuracy_score, confusion_matrix
from LearningAlgorithms import ClassificationAlgorithms

# Plot settings
plt.style.use("fivethirtyeight")
plt.rcParams["figure.figsize"] = (20, 5)
plt.rcParams["figure.dpi"] = 100
plt.rcParams["lines.linewidth"] = 2

df = pd.read_pickle("../../data/interim/03_data_features.pkl")

# Creating Traing and Testing sets
df_train = df.drop(["participant", "category", "set"], axis=1)

X = df_train.drop("label", axis=1)
y = df_train["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

fig, ax = plt.subplots(figsize=(10, 5))
df_train["label"].value_counts().plot(
    kind="bar", ax=ax, color="lightblue", label="Total"
)
y_train.value_counts().plot(kind="bar", ax=ax, color="dodgerblue", label="Train")
y_test.value_counts().plot(kind="bar", ax=ax, color="royalblue", label="Test")
plt.legend()
plt.show()

# Splitting features into subsets
basic_features = ["acc_x", "acc_y", "acc_z", "gyr_x", "gyr_y", "gyr_z"]
square_features = ["acc_r", "gyr_r"]
pca_features = ["pca_1", "pca_2", "pca_3"]
time_features = [f for f in df_train.columns if "_temp_" in f]
freq_features = [f for f in df_train.columns if ("_freq" in f) or ("_pse" in f)]
cluster_features = ["cluster"]

print(f"Basic features: {len(basic_features)}")
print(f"Square features: {len(square_features)}")
print(f"PCA features: {len(pca_features)}")
print(f"Time features: {len(time_features)}")
print(f"Freq features: {len(freq_features)}")
print(f"Cluster features: {len(cluster_features)}")

feature_set_1 = list(set(basic_features))
feature_set_2 = list(set(basic_features + square_features + pca_features))
feature_set_3 = list(set(feature_set_2 + time_features))
feature_set_4 = list(set(feature_set_3 + freq_features + cluster_features))

# Performing forward feature selection using simple decision tree
learner = ClassificationAlgorithms()

max_features = 10
selected_features, ordered_features, ordered_scores = learner.forward_selection(max_features, X_train, y_train)

selected_features = [
    'pca_1',
    'gyr_r_freq_0.0_Hz_ws_14',
    'acc_x_freq_0.0_Hz_ws_14',
    'acc_z_freq_0.0_Hz_ws_14',
    'acc_z_temp_mean_ws_5',
    'gyr_r_freq_2.143_Hz_ws_14',
    'gyr_x_freq_0.714_Hz_ws_14',
    'gyr_r_max_freq',
    'acc_r',
    'gyr_z_freq_1.071_Hz_ws_14'
]

plt.figure(figsize=(10, 5))
plt.plot(np.arange(1, max_features + 1, 1),ordered_scores)
plt.xlabel("Number of features")
plt.ylabel("Accuracy")
plt.xticks(np.arange(1, max_features + 1, 1))
plt.show()

# Grid search for finding best hyperparameters and model selection

possible_feature_sets = [
    feature_set_1,
    feature_set_2,
    feature_set_3,
    feature_set_4,
    selected_features
]

feature_names = [
    "Feature Set 1",
    "Feature Set 2",
    "Feature Set 3",
    "Feature Set 4",
    "Selected Features"
]

iterations = 1
score_df = pd.DataFrame()

# Loop over feature sets and feature names
for i, f in zip(range(len(possible_feature_sets)), feature_names):
    print("Feature set:", f)
    selected_train_X = X_train[possible_feature_sets[i]]
    selected_test_X = X_test[possible_feature_sets[i]]

    # First run non-deterministic classifiers to average their score
    performance_test_nn = 0
    performance_test_rf = 0

    for it in range(iterations):
        print("\tTraining neural network,", it)
        nn_results = learner.feedforward_neural_network(selected_train_X, y_train, selected_test_X, gridsearch=False)
        performance_test_nn += accuracy_score(y_test, nn_results[1])

        print("\tTraining random forest,", it)
        rf_results = learner.random_forest(selected_train_X, y_train, selected_test_X, gridsearch=True)
        performance_test_rf += accuracy_score(y_test, rf_results[1])

    performance_test_nn /= iterations
    performance_test_rf /= iterations

    # Run deterministic classifiers
    print("\tTraining KNN")
    try:
        knn_results = learner.k_nearest_neighbor(selected_train_X, y_train, selected_test_X, gridsearch=True)
        performance_test_knn = accuracy_score(y_test, knn_results[1])
    except AttributeError as e:
        print(f"Error with KNN: {e}")
        performance_test_knn = None  # Handle the error and continue

    print("\tTraining decision tree")
    dt_results = learner.decision_tree(selected_train_X, y_train, selected_test_X, gridsearch=True)
    performance_test_dt = accuracy_score(y_test, dt_results[1])

    print("\tTraining naive bayes")
    nb_results = learner.naive_bayes(selected_train_X, y_train, selected_test_X)
    performance_test_nb = accuracy_score(y_test, nb_results[1])

    # Save results to DataFrame
    models = ["NN", "RF", "KNN", "DT", "NB"]
    accuracies = [
        performance_test_nn,
        performance_test_rf,
        performance_test_knn,
        performance_test_dt,
        performance_test_nb,
    ]
    new_scores = pd.DataFrame({
        "model": models,
        "feature_set": f,
        "accuracy": accuracies
    })
    score_df = pd.concat([score_df, new_scores], ignore_index=True)
