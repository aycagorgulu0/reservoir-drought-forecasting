# BigML clustering (Task 3)

Same table as notebook 1.1 (reports/deliverable_2/tables/reservoir_features.csv), K-means, k = 2, reservoir and basin excluded, fields auto-scaled.

- bigml_clusters.csv: batch centroid, one row per reservoir with its BigML cluster
- bigml_2_cluster*.png, bigml_3_cluster_green.png, bigml_4_cluster_pink.png: cluster view (35 and 73 reservoirs)
- bigml_5_batch_centroid.png: batch centroid output
- first_run_wrong_locale/: first attempt, read with the Turkish browser locale (0.1266 became 1266); kept to document the problem, see notebook 1.1

Agreement with Python k-means: 101 of 108 reservoirs, adjusted Rand index 0.75.
