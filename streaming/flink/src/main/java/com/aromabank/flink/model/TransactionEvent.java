package com.aromabank.flink.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;

/**
 * POJO for incoming financial transaction streaming event.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class TransactionEvent implements Serializable {
    private static final long serialVersionUID = 1L;

    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("account_id")
    private String accountId;

    @JsonProperty("counterparty_account_id")
    private String counterpartyAccountId;

    @JsonProperty("customer_id")
    private int customerId;

    @JsonProperty("ecommerce_order_id")
    private String ecommerceOrderId;

    @JsonProperty("transaction_type")
    private String transactionType;

    @JsonProperty("channel")
    private String channel;

    @JsonProperty("status")
    private String status;

    @JsonProperty("amount_original")
    private double amountOriginal;

    @JsonProperty("currency_original")
    private String currencyOriginal;

    @JsonProperty("amount_pln")
    private double amountPln;

    @JsonProperty("city")
    private String city;

    @JsonProperty("country")
    private String country;

    @JsonProperty("timestamp_utc")
    private String timestampUtc;

    @JsonProperty("is_synthetic_fraud")
    private boolean isSyntheticFraud;

    @JsonProperty("fraud_pattern")
    private String fraudPattern;

    @JsonProperty("risk_score")
    private double riskScore;

    public TransactionEvent() {}

    // Getters and Setters
    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }

    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }

    public String getCounterpartyAccountId() { return counterpartyAccountId; }
    public void setCounterpartyAccountId(String counterpartyAccountId) { this.counterpartyAccountId = counterpartyAccountId; }

    public int getCustomerId() { return customerId; }
    public void setCustomerId(int customerId) { this.customerId = customerId; }

    public String getEcommerceOrderId() { return ecommerceOrderId; }
    public void setEcommerceOrderId(String ecommerceOrderId) { this.ecommerceOrderId = ecommerceOrderId; }

    public String getTransactionType() { return transactionType; }
    public void setTransactionType(String transactionType) { this.transactionType = transactionType; }

    public String getChannel() { return channel; }
    public void setChannel(String channel) { this.channel = channel; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public double getAmountOriginal() { return amountOriginal; }
    public void setAmountOriginal(double amountOriginal) { this.amountOriginal = amountOriginal; }

    public String getCurrencyOriginal() { return currencyOriginal; }
    public void setCurrencyOriginal(String currencyOriginal) { this.currencyOriginal = currencyOriginal; }

    public double getAmountPln() { return amountPln; }
    public void setAmountPln(double amountPln) { this.amountPln = amountPln; }

    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }

    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    public String getTimestampUtc() { return timestampUtc; }
    public void setTimestampUtc(String timestampUtc) { this.timestampUtc = timestampUtc; }

    public boolean isSyntheticFraud() { return isSyntheticFraud; }
    public void setSyntheticFraud(boolean syntheticFraud) { isSyntheticFraud = syntheticFraud; }

    public String getFraudPattern() { return fraudPattern; }
    public void setFraudPattern(String fraudPattern) { this.fraudPattern = fraudPattern; }

    public double getRiskScore() { return riskScore; }
    public void setRiskScore(double riskScore) { this.riskScore = riskScore; }
}
