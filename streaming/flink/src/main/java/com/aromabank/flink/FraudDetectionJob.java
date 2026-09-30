package com.aromabank.flink;

import com.aromabank.flink.model.FraudAlertEvent;
import com.aromabank.flink.model.TransactionEvent;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Apache Flink Real-Time Stateful Stream Processing Job.
 * Consumes financial transactions from Kafka (bank.transactions.raw),
 * executes stateful sliding-window velocity checks & amount anomaly detection,
 * and emits real-time fraud alerts to bank.fraud.alerts.
 */
public class FraudDetectionJob {

    private static final String DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String INPUT_TOPIC = "bank.transactions.raw";
    private static final String OUTPUT_TOPIC = "bank.fraud.alerts";
    private static final String CONSUMER_GROUP = "flink-fraud-detector-group";

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.getConfig().setAutoWatermarkInterval(200);

        String bootstrapServers = args.length > 0 ? args[0] : DEFAULT_BOOTSTRAP_SERVERS;

        // 1. Configure Kafka Source
        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers(bootstrapServers)
                .setTopics(INPUT_TOPIC)
                .setGroupId(CONSUMER_GROUP)
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        // 2. Read stream and deserialize JSON to TransactionEvent
        DataStream<String> rawStream = env.fromSource(source, WatermarkStrategy.noWatermarks(), "Kafka-Transactions-Source");

        DataStream<TransactionEvent> txnStream = rawStream.map(new MapFunction<String, TransactionEvent>() {
            private final transient ObjectMapper mapper = new ObjectMapper();

            @Override
            public TransactionEvent map(String json) {
                try {
                    return mapper.readValue(json, TransactionEvent.class);
                } catch (Exception e) {
                    return null; // Fault-tolerant skip malformed
                }
            }
        }).filter(t -> t != null && t.getAccountId() != null);

        // 3. Key by Account ID and execute stateful velocity & amount anomaly detection
        DataStream<FraudAlertEvent> alertStream = txnStream
                .keyBy(TransactionEvent::getAccountId)
                .process(new VelocityAndOutlierFraudDetector());

        // 4. Print alerts to standard out for immediate observability
        alertStream.map(alert -> String.format("🚨 [FLINK FRAUD ALERT] %s | Acc: %s | Rule: %s | Amount: %.2f PLN | Confidence: %.2f",
                alert.getAlertId(), alert.getAccountId(), alert.getRuleTriggered(), alert.getAmountPln(), alert.getConfidenceScore()))
                .print();

        // 5. Configure Kafka Sink for downstream microservices (e.g. Databricks, SMS alert, Blocking)
        KafkaRecordSerializationSchema<String> serializer = KafkaRecordSerializationSchema.builder()
                .setTopic(OUTPUT_TOPIC)
                .setValueSerializationSchema(new SimpleStringSchema())
                .build();

        KafkaSink<String> kafkaSink = KafkaSink.<String>builder()
                .setBootstrapServers(bootstrapServers)
                .setRecordSerializer(serializer)
                .build();

        DataStream<String> alertJsonStream = alertStream.map(new MapFunction<FraudAlertEvent, String>() {
            private final transient ObjectMapper mapper = new ObjectMapper();

            @Override
            public String map(FraudAlertEvent alert) throws Exception {
                return mapper.writeValueAsString(alert);
            }
        });

        alertJsonStream.sinkTo(kafkaSink);

        System.out.println("⚡ Starting AromaBank Apache Flink Real-Time Streaming Job...");
        env.execute("AromaBank-Flink-FraudDetection");
    }

    /**
     * Stateful KeyedProcessFunction:
     * - Retains timestamps of recent transactions in state
     * - Triggers VELOCITY alert if >3 transactions happen within 30 seconds
     * - Triggers OUTLIER alert if amount exceeds 10,000 PLN or synthetic flag is present
     */
    public static class VelocityAndOutlierFraudDetector extends KeyedProcessFunction<String, TransactionEvent, FraudAlertEvent> {

        private transient ListState<Long> recentTimestampsState;
        private static final long VELOCITY_WINDOW_MS = 30_000L; // 30 seconds
        private static final int VELOCITY_THRESHOLD = 3;
        private static final double LARGE_AMOUNT_THRESHOLD = 10_000.0;

        @Override
        public void open(Configuration parameters) {
            ListStateDescriptor<Long> descriptor = new ListStateDescriptor<>(
                    "recentTimestamps",
                    TypeInformation.of(Long.class)
            );
            recentTimestampsState = getRuntimeContext().getListState(descriptor);
        }

        @Override
        public void processElement(TransactionEvent txn, Context ctx, Collector<FraudAlertEvent> out) throws Exception {
            long currentTimestamp = Instant.now().toEpochMilli();

            // 1. Maintain sliding window of event timestamps in state
            List<Long> updatedList = new ArrayList<>();
            for (Long ts : recentTimestampsState.get()) {
                if (currentTimestamp - ts <= VELOCITY_WINDOW_MS) {
                    updatedList.add(ts);
                }
            }
            updatedList.add(currentTimestamp);
            recentTimestampsState.update(updatedList);

            // Rule 1: High-Velocity Attack (>3 transactions in 30s)
            if (updatedList.size() >= VELOCITY_THRESHOLD) {
                out.collect(new FraudAlertEvent(
                        "FRD-" + UUID.randomUUID().toString().substring(0, 8),
                        txn.getAccountId(),
                        txn.getTransactionId(),
                        "RAPID_VELOCITY_BURST",
                        txn.getAmountPln(),
                        0.96,
                        "BLOCK_CARD_IMMEDIATE",
                        Instant.now().toString()
                ));
            }

            // Rule 2: Sudden Large Amount Outlier / Structuring Threshold
            if (txn.getAmountPln() >= LARGE_AMOUNT_THRESHOLD) {
                out.collect(new FraudAlertEvent(
                        "FRD-" + UUID.randomUUID().toString().substring(0, 8),
                        txn.getAccountId(),
                        txn.getTransactionId(),
                        "LARGE_AMOUNT_OUTLIER",
                        txn.getAmountPln(),
                        0.88,
                        "STEP_UP_TWO_FACTOR_SMS",
                        Instant.now().toString()
                ));
            }

            // Rule 3: Geo-Impossible Travel or Synthetic Fraud Flag
            if (txn.isSyntheticFraud() && "GEO_IMPOSSIBLE".equals(txn.getFraudPattern())) {
                out.collect(new FraudAlertEvent(
                        "FRD-" + UUID.randomUUID().toString().substring(0, 8),
                        txn.getAccountId(),
                        txn.getTransactionId(),
                        "IMPOSSIBLE_GEO_TRAVEL",
                        txn.getAmountPln(),
                        0.99,
                        "BLOCK_AND_NOTIFY_CALL_CENTER",
                        Instant.now().toString()
                ));
            }
        }
    }
}
