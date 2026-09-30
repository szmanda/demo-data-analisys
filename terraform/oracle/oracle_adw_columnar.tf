# Terraform OCI Manifest: Oracle Autonomous Data Warehouse (ADW)
# Utilizes Oracle In-Memory Columnar format and Hybrid Columnar Compression (HCC)
# for high-performance analytical queries and long-term financial data archiving.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.20.0"
    }
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCI Compartment OCID"
  default     = "ocid1.compartment.oc1..example"
}

resource "oci_database_autonomous_database" "oracle_adw_columnar" {
  compartment_id           = var.compartment_ocid
  db_name                  = "aromabankadw"
  display_name             = "AromaBank-Autonomous-Data-Warehouse-Columnar"
  db_workload              = "DW" # DW = Data Warehouse (Enables Hybrid Columnar Compression)
  cpu_core_count           = 1
  data_storage_size_in_tbs = 1
  is_auto_scaling_enabled  = true
  is_free_tier             = true # Eligible for Oracle Cloud Free Tier
  admin_password           = "StrongOracleAdminPassword2024!"

  # Columnar In-Memory allocation for vector processing
  in_memory_percentage     = 50

  license_model            = "LICENSE_INCLUDED"

  tags = {
    "Project"      = "AromaBank"
    "StorageModel" = "Distributed-Columnar-HCC"
  }
}

output "adw_connection_urls" {
  value       = oci_database_autonomous_database.oracle_adw_columnar.connection_urls
  description = "JDBC and Oracle SQL Developer connection endpoints"
}
