# Connect image with the JDBC sink plugin pre-installed.
#
# This optional service exists to show the "no custom code" path to the same
# warehouse: Kafka Connect reads the topic and upserts straight into Postgres.
# It needs internet access on first build to fetch the connector from
# Confluent Hub, which is why it is behind the `connect` Compose profile.
FROM confluentinc/cp-kafka-connect-base:7.7.1

RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.6
