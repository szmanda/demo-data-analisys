package com.aromabank.flink.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;

/**
 * POJO for fraud alert events emitted by Apache Flink real-time rules engine.
 */
public class FraudAlertEvent implements Serializable {
    private static final long serialVersionUID = 1L;

    @JsonProperty("alert_id")
    private String alertId;

    @JsonProperty("account_id")
    private String accountId;

    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("rule_triggered")
    private String ruleTriggered;

    @JsonProperty("amount_pln")
    private double amountPln;

    @JsonProperty("confidence_score")
    private double confidenceScore;

    @JsonProperty("action_recommended")
    private String actionRecommended;

    @JsonProperty("detection_engine")
    private String detectionEngine = "Apache-Flink-Java-CEP";

    @JsonProperty("alert_timestamp_utc")
    private String alertTimestampUtc;

    public FraudAlertEvent() {}

    public FraudAlertEvent(String alertId, String accountId, String transactionId,
                           String ruleTriggered, double amountPln, double confidenceScore,
                           String actionRecommended, String alertTimestampUtc) {
        this.alertId = alertId;
        this.accountId = accountId;
        this.transactionId = transactionId;
        this.ruleTriggered = ruleTriggered;
        this.amountPln = amountPln;
        this.confidenceScore = confidenceScore;
        this.actionRecommended = actionRecommended;
        this.alertTimestampUtc = alertTimestampUtc;
    }

    public String getAlertId() { return alertId; }
    public String getAccountId() { return accountId; }
    public String getTransactionId() { return transactionId; }
    public String getRuleTriggered() { return ruleTriggered; }
    public double getAmountPln() { return amountPln; }
    public double getConfidenceScore() { return confidenceScore; }
    public String getActionRecommended() { return actionRecommended; }
    public String getDetectionEngine() { return detectionEngine; }
    public String getAlertTimestampUtc() { return alertTimestampUtc; }
}
