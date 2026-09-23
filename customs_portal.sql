-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: customs_portal
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `approval_requests`
--

DROP TABLE IF EXISTS `approval_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `approval_requests` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reference_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reference_id` bigint DEFAULT NULL,
  `requested_by` int DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  `status` enum('pending','approved','rejected') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `approved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_approval_requested_by` (`requested_by`),
  KEY `fk_approval_approved_by` (`approved_by`),
  KEY `idx_approval_status` (`status`),
  CONSTRAINT `fk_approval_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_approval_requested_by` FOREIGN KEY (`requested_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `approval_requests`
--

LOCK TABLES `approval_requests` WRITE;
/*!40000 ALTER TABLE `approval_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `approval_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets`
--

DROP TABLE IF EXISTS `assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `asset_code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int DEFAULT NULL,
  `asset_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `serial_number` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `purchase_cost` decimal(18,2) DEFAULT NULL,
  `current_value` decimal(18,2) DEFAULT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('active','maintenance','disposed') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_code` (`asset_code`),
  KEY `idx_assets_status` (`status`),
  KEY `idx_assets_item` (`item_id`),
  CONSTRAINT `fk_asset_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets`
--

LOCK TABLES `assets` WRITE;
/*!40000 ALTER TABLE `assets` DISABLE KEYS */;
/*!40000 ALTER TABLE `assets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `table_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `record_id` bigint DEFAULT NULL,
  `old_values` json DEFAULT NULL,
  `new_values` json DEFAULT NULL,
  `ip_address` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_audit_user` (`user_id`),
  KEY `idx_audit_table` (`table_name`),
  CONSTRAINT `fk_audit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `brands`
--

DROP TABLE IF EXISTS `brands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brands` (
  `id` int NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `brand_name` (`brand_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brands`
--

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
INSERT INTO `brands` VALUES (1,'General',NULL,'2026-05-30 21:16:14'),(2,'Siemens',NULL,'2026-05-30 21:16:14'),(3,'Schneider',NULL,'2026-05-30 21:16:14'),(4,'ABB',NULL,'2026-05-30 21:16:14');
/*!40000 ALTER TABLE `brands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int DEFAULT NULL,
  `category_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category_name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category_name_en` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `category_code` (`category_code`),
  KEY `idx_categories_parent` (`parent_id`),
  CONSTRAINT `fk_categories_parent` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,NULL,NULL,'أجهزة',NULL,NULL,'2026-05-31 12:23:19');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `company_info`
--

DROP TABLE IF EXISTS `company_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_name_ar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_name_en` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `phone` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `website` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tax_number` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `logo_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `company_info`
--

LOCK TABLES `company_info` WRITE;
/*!40000 ALTER TABLE `company_info` DISABLE KEYS */;
INSERT INTO `company_info` VALUES (1,'شركة نابيسكو','NAPESCO',NULL,NULL,NULL,NULL,NULL,NULL,'2026-05-30 21:23:26');
/*!40000 ALTER TABLE `company_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customs_declarations`
--

DROP TABLE IF EXISTS `customs_declarations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customs_declarations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `declaration_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `declaration_date` date NOT NULL,
  `inbound_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `importer_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `exporter_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `origin_country` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `destination_country` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shipment_reference` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `acid` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_value` decimal(18,2) DEFAULT '0.00',
  `customs_fee` decimal(18,2) DEFAULT '0.00',
  `status` enum('draft','submitted','under_review','approved','rejected','cleared') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `created_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `regime_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `declaration_no` (`declaration_no`),
  KEY `fk_customs_created_by` (`created_by`),
  KEY `idx_customs_status` (`status`),
  KEY `idx_customs_date` (`declaration_date`),
  CONSTRAINT `fk_customs_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customs_declarations`
--

LOCK TABLES `customs_declarations` WRITE;
/*!40000 ALTER TABLE `customs_declarations` DISABLE KEYS */;
INSERT INTO `customs_declarations` VALUES (1,'CUS-2026-0001','2026-05-31',NULL,'NAPESCO',NULL,NULL,NULL,NULL,NULL,0.00,0.00,'draft',NULL,'2026-05-30 21:21:26','2026-05-30 21:21:26',NULL);
/*!40000 ALTER TABLE `customs_declarations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customs_items`
--

DROP TABLE IF EXISTS `customs_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customs_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `declaration_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `unit_price` decimal(18,4) DEFAULT '0.0000',
  `duty_amount` decimal(18,2) DEFAULT '0.00',
  `tax_amount` decimal(18,2) DEFAULT '0.00',
  PRIMARY KEY (`id`),
  KEY `fk_customs_items_declaration` (`declaration_id`),
  KEY `idx_customs_items_item` (`item_id`),
  CONSTRAINT `fk_customs_items_declaration` FOREIGN KEY (`declaration_id`) REFERENCES `customs_declarations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_customs_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customs_items`
--

LOCK TABLES `customs_items` WRITE;
/*!40000 ALTER TABLE `customs_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `customs_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goods_receipt_items`
--

DROP TABLE IF EXISTS `goods_receipt_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goods_receipt_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `receipt_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `ordered_qty` decimal(18,2) DEFAULT NULL,
  `received_qty` decimal(18,2) NOT NULL,
  `unit_cost` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_receipt_items_receipt` (`receipt_id`),
  KEY `idx_receipt_items_item` (`item_id`),
  CONSTRAINT `fk_receipt_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_receipt_items_receipt` FOREIGN KEY (`receipt_id`) REFERENCES `goods_receipts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goods_receipt_items`
--

LOCK TABLES `goods_receipt_items` WRITE;
/*!40000 ALTER TABLE `goods_receipt_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `goods_receipt_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goods_receipts`
--

DROP TABLE IF EXISTS `goods_receipts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goods_receipts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `receipt_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  `store_id` int NOT NULL,
  `receipt_date` date NOT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `received_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `receipt_no` (`receipt_no`),
  KEY `fk_receipt_user` (`received_by`),
  KEY `idx_receipt_po` (`purchase_order_id`),
  KEY `idx_receipt_store` (`store_id`),
  CONSTRAINT `fk_receipt_po` FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_receipt_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_receipt_user` FOREIGN KEY (`received_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goods_receipts`
--

LOCK TABLES `goods_receipts` WRITE;
/*!40000 ALTER TABLE `goods_receipts` DISABLE KEYS */;
/*!40000 ALTER TABLE `goods_receipts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_count_items`
--

DROP TABLE IF EXISTS `inventory_count_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_count_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `inventory_count_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `system_qty` decimal(18,2) DEFAULT '0.00',
  `counted_qty` decimal(18,2) DEFAULT '0.00',
  `variance_qty` decimal(18,2) DEFAULT '0.00',
  `remarks` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `fk_inventory_count_items_count` (`inventory_count_id`),
  KEY `fk_inventory_count_items_item` (`item_id`),
  CONSTRAINT `fk_inventory_count_items_count` FOREIGN KEY (`inventory_count_id`) REFERENCES `inventory_counts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_inventory_count_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_count_items`
--

LOCK TABLES `inventory_count_items` WRITE;
/*!40000 ALTER TABLE `inventory_count_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventory_count_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_counts`
--

DROP TABLE IF EXISTS `inventory_counts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_counts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `count_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `store_id` int NOT NULL,
  `count_date` date NOT NULL,
  `status` enum('draft','in_progress','approved','closed') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `counted_by` int DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `count_no` (`count_no`),
  KEY `fk_inventory_count_user` (`counted_by`),
  KEY `fk_inventory_count_approved` (`approved_by`),
  KEY `idx_inventory_counts_store` (`store_id`),
  CONSTRAINT `fk_inventory_count_approved` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_inventory_count_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_inventory_count_user` FOREIGN KEY (`counted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_counts`
--

LOCK TABLES `inventory_counts` WRITE;
/*!40000 ALTER TABLE `inventory_counts` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventory_counts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issue_voucher_items`
--

DROP TABLE IF EXISTS `issue_voucher_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issue_voucher_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `voucher_id` int DEFAULT NULL,
  `item_id` int DEFAULT NULL,
  `qty` decimal(12,2) DEFAULT NULL,
  `unit_price` decimal(12,2) DEFAULT NULL,
  `total` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `voucher_id` (`voucher_id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `issue_voucher_items_ibfk_1` FOREIGN KEY (`voucher_id`) REFERENCES `issue_vouchers` (`id`),
  CONSTRAINT `issue_voucher_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issue_voucher_items`
--

LOCK TABLES `issue_voucher_items` WRITE;
/*!40000 ALTER TABLE `issue_voucher_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `issue_voucher_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issue_vouchers`
--

DROP TABLE IF EXISTS `issue_vouchers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issue_vouchers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `voucher_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `issue_date` date DEFAULT NULL,
  `department` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `receiver_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voucher_no` (`voucher_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issue_vouchers`
--

LOCK TABLES `issue_vouchers` WRITE;
/*!40000 ALTER TABLE `issue_vouchers` DISABLE KEYS */;
/*!40000 ALTER TABLE `issue_vouchers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_images`
--

DROP TABLE IF EXISTS `item_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_images` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `image_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_default` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_item_images_item` (`item_id`),
  CONSTRAINT `fk_item_images_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_images`
--

LOCK TABLES `item_images` WRITE;
/*!40000 ALTER TABLE `item_images` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_movements`
--

DROP TABLE IF EXISTS `item_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_movements` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `store_id` int NOT NULL,
  `movement_type` enum('opening_balance','purchase','issue','transfer_in','transfer_out','adjustment_plus','adjustment_minus','maintenance_issue','maintenance_return') COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `unit_cost` decimal(18,4) DEFAULT '0.0000',
  `total_cost` decimal(18,4) DEFAULT '0.0000',
  `reference_no` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_movements_user` (`created_by`),
  KEY `idx_movements_item` (`item_id`),
  KEY `idx_movements_store` (`store_id`),
  KEY `idx_movements_type` (`movement_type`),
  KEY `idx_movements_date` (`created_at`),
  CONSTRAINT `fk_movements_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_movements_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_movements_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_movements`
--

LOCK TABLES `item_movements` WRITE;
/*!40000 ALTER TABLE `item_movements` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_movements` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_stock_after_insert` AFTER INSERT ON `item_movements` FOR EACH ROW BEGIN

    IF NEW.movement_type IN
    (
        'opening_balance',
        'purchase',
        'transfer_in',
        'adjustment_plus',
        'maintenance_return'
    )
    THEN

        INSERT INTO store_items
        (
            store_id,
            item_id,
            quantity,
            last_movement_date
        )
        VALUES
        (
            NEW.store_id,
            NEW.item_id,
            NEW.quantity,
            NOW()
        )

        ON DUPLICATE KEY UPDATE
            quantity = quantity + NEW.quantity,
            last_movement_date = NOW();

    END IF;

    IF NEW.movement_type IN
    (
        'issue',
        'transfer_out',
        'adjustment_minus',
        'maintenance_issue'
    )
    THEN

        UPDATE store_items
        SET quantity = quantity - NEW.quantity,
            last_movement_date = NOW()
        WHERE store_id = NEW.store_id
        AND item_id = NEW.item_id;

    END IF;

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `unit_id` int NOT NULL,
  `brand_id` int DEFAULT NULL,
  `item_code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `barcode` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `item_name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(12,2) DEFAULT '0.00',
  `weight` decimal(12,3) DEFAULT '0.000',
  `item_name_en` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `specification` text COLLATE utf8mb4_unicode_ci,
  `min_qty` decimal(18,2) DEFAULT '0.00',
  `max_qty` decimal(18,2) DEFAULT '0.00',
  `standard_cost` decimal(18,4) DEFAULT '0.0000',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `item_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `department` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'local_purchases',
  `receipt_no` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `po_number` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `qty` decimal(12,2) DEFAULT '0.00',
  `shipping_cost` decimal(12,2) DEFAULT '0.00',
  `unit_price` decimal(12,2) DEFAULT '0.00',
  `total_cost` decimal(12,2) DEFAULT '0.00',
  `current_stock` decimal(12,2) DEFAULT '0.00',
  `current_balance` decimal(15,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_code` (`item_code`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `idx_items_category` (`category_id`),
  KEY `idx_items_unit` (`unit_id`),
  KEY `idx_items_brand` (`brand_id`),
  KEY `idx_items_name_ar` (`item_name_ar`),
  CONSTRAINT `fk_items_brand` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_items_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_items_unit` FOREIGN KEY (`unit_id`) REFERENCES `units` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES (3,1,1,NULL,'ITM001',NULL,'جهاز كمبيوتر',0.00,0.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 12:30:58','2026-05-31 12:30:58',NULL,NULL,NULL,0.00,0.00,0.00,0.00,0.00),(4,1,1,NULL,'26-1',NULL,'labtop hp',0.00,0.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 12:44:29','2026-05-31 12:44:29',NULL,NULL,NULL,0.00,0.00,0.00,0.00,0.00),(10,1,1,NULL,'236',NULL,'كاب باسم',0.00,0.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 13:13:51','2026-05-31 13:16:33',NULL,NULL,NULL,0.00,0.00,0.00,0.00,0.00),(13,1,1,NULL,'2026',NULL,'كورة قدم باسم',3000.00,2000.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 13:59:53','2026-05-31 13:59:53',NULL,NULL,NULL,0.00,0.00,0.00,0.00,0.00),(22,1,1,NULL,'26-9',NULL,'كورة قدم باسمتا',300.01,20.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 14:11:33','2026-05-31 14:27:37',NULL,NULL,NULL,0.00,0.00,0.00,0.00,0.00),(24,1,1,NULL,'26-31',NULL,'موبايل',0.00,6.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 15:42:34','2026-05-31 15:42:34','مخزون','2-2026','2-2026',3.00,130.00,100.00,430.00,0.00),(27,1,5,NULL,'26-333',NULL,'موبايل',6500.00,7.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 15:44:08','2026-05-31 15:44:08','مخزون','2-2026','2-2026',6.00,500.00,1000.00,6500.00,0.00),(30,1,1,NULL,'26-189',NULL,'كاميرات واي فاي',1500.00,1.000,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 17:08:47','2026-05-31 17:08:47','مخزون','1-2026','1-2026',60.00,0.00,150.00,9000.00,0.00),(31,1,1,NULL,'26-40',NULL,'لاب توب توشيبا مستعمل',6700.00,1.500,NULL,NULL,0.00,0.00,0.0000,1,'2026-05-31 17:54:21','2026-05-31 17:54:21','مستعمل','1-2024','2-2024',1.00,150.00,6400.00,6550.00,0.00);
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `supplier_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `supplier_code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_suppliers_code` (`supplier_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `job_items`
--

DROP TABLE IF EXISTS `job_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `unit_cost` decimal(18,4) DEFAULT '0.0000',
  PRIMARY KEY (`id`),
  KEY `fk_job_items_job` (`job_id`),
  KEY `idx_job_items_item` (`item_id`),
  CONSTRAINT `fk_job_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_job_items_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job_items`
--

LOCK TABLES `job_items` WRITE;
/*!40000 ALTER TABLE `job_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `job_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `maintenance_request_id` bigint NOT NULL,
  `job_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `assigned_to` int DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `status` enum('open','assigned','in_progress','completed','closed') COLLATE utf8mb4_unicode_ci DEFAULT 'open',
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_no` (`job_no`),
  KEY `fk_jobs_request` (`maintenance_request_id`),
  KEY `fk_jobs_assigned_to` (`assigned_to`),
  KEY `idx_jobs_status` (`status`),
  CONSTRAINT `fk_jobs_assigned_to` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_jobs_request` FOREIGN KEY (`maintenance_request_id`) REFERENCES `maintenance_requests` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `maintenance_requests`
--

DROP TABLE IF EXISTS `maintenance_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `maintenance_requests` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `request_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `priority` enum('low','medium','high','critical') COLLATE utf8mb4_unicode_ci DEFAULT 'medium',
  `status` enum('open','assigned','in_progress','completed','closed') COLLATE utf8mb4_unicode_ci DEFAULT 'open',
  `requested_by` int DEFAULT NULL,
  `assigned_to` int DEFAULT NULL,
  `request_date` date DEFAULT NULL,
  `completion_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `request_no` (`request_no`),
  KEY `fk_maintenance_requested_by` (`requested_by`),
  KEY `fk_maintenance_assigned_to` (`assigned_to`),
  KEY `idx_maintenance_status` (`status`),
  KEY `idx_maintenance_priority` (`priority`),
  CONSTRAINT `fk_maintenance_assigned_to` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_maintenance_requested_by` FOREIGN KEY (`requested_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `maintenance_requests`
--

LOCK TABLES `maintenance_requests` WRITE;
/*!40000 ALTER TABLE `maintenance_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `maintenance_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci,
  `is_read` tinyint(1) DEFAULT '0',
  `read_at` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_notifications_user` (`user_id`),
  KEY `idx_notifications_read` (`is_read`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `permission_key` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `permission_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `module_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `permission_key` (`permission_key`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions`
--

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` VALUES (1,'dashboard.view','View Dashboard','Dashboard','2026-05-30 21:10:29'),(2,'users.view','View Users','Users','2026-05-30 21:10:29'),(3,'users.create','Create Users','Users','2026-05-30 21:10:29'),(4,'users.edit','Edit Users','Users','2026-05-30 21:10:29'),(5,'users.delete','Delete Users','Users','2026-05-30 21:10:29'),(6,'inventory.view','View Inventory','Inventory','2026-05-30 21:10:29'),(7,'inventory.create','Create Inventory','Inventory','2026-05-30 21:10:29'),(8,'inventory.edit','Edit Inventory','Inventory','2026-05-30 21:10:29'),(9,'inventory.delete','Delete Inventory','Inventory','2026-05-30 21:10:29'),(10,'stores.view','View Stores','Stores','2026-05-30 21:10:29'),(11,'stores.create','Create Stores','Stores','2026-05-30 21:10:29'),(12,'stores.edit','Edit Stores','Stores','2026-05-30 21:10:29'),(13,'purchase.view','View Purchase Orders','Purchasing','2026-05-30 21:10:29'),(14,'purchase.create','Create Purchase Orders','Purchasing','2026-05-30 21:10:29'),(15,'purchase.approve','Approve Purchase Orders','Purchasing','2026-05-30 21:10:29'),(16,'customs.view','View Customs','Customs','2026-05-30 21:10:29'),(17,'customs.create','Create Customs Declaration','Customs','2026-05-30 21:10:29'),(18,'maintenance.view','View Maintenance','Maintenance','2026-05-30 21:10:29'),(19,'maintenance.create','Create Maintenance Request','Maintenance','2026-05-30 21:10:29'),(20,'reports.view','View Reports','Reports','2026-05-30 21:10:29'),(21,'settings.view','View Settings','Settings','2026-05-30 21:10:29'),(22,'settings.edit','Edit Settings','Settings','2026-05-30 21:10:29');
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_order_items`
--

DROP TABLE IF EXISTS `purchase_order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_order_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `purchase_order_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `unit_price` decimal(18,4) NOT NULL,
  `line_total` decimal(18,4) NOT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_po_item` (`purchase_order_id`,`item_id`),
  KEY `idx_po_items_item` (`item_id`),
  CONSTRAINT `fk_po_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_po_items_po` FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_order_items`
--

LOCK TABLES `purchase_order_items` WRITE;
/*!40000 ALTER TABLE `purchase_order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_orders`
--

DROP TABLE IF EXISTS `purchase_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `po_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `vendor_id` int NOT NULL,
  `order_date` date NOT NULL,
  `expected_delivery_date` date DEFAULT NULL,
  `status` enum('draft','submitted','approved','partially_received','received','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `subtotal` decimal(18,2) DEFAULT '0.00',
  `tax_amount` decimal(18,2) DEFAULT '0.00',
  `total_amount` decimal(18,2) DEFAULT '0.00',
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` int DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `po_number` (`po_number`),
  KEY `fk_po_created_by` (`created_by`),
  KEY `fk_po_approved_by` (`approved_by`),
  KEY `idx_po_vendor` (`vendor_id`),
  KEY `idx_po_status` (`status`),
  KEY `idx_po_date` (`order_date`),
  CONSTRAINT `fk_po_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_po_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_po_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendors` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_orders`
--

LOCK TABLES `purchase_orders` WRITE;
/*!40000 ALTER TABLE `purchase_orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_permissions`
--

DROP TABLE IF EXISTS `role_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_permissions` (
  `role_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`role_id`,`permission_id`),
  KEY `fk_role_permissions_permission` (`permission_id`),
  CONSTRAINT `fk_role_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_role_permissions_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_permissions`
--

LOCK TABLES `role_permissions` WRITE;
/*!40000 ALTER TABLE `role_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `role_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Admin','System Administrator','2026-05-30 21:10:29'),(2,'Manager','Department Manager','2026-05-30 21:10:29'),(3,'Storekeeper','Warehouse User','2026-05-30 21:10:29'),(4,'Purchasing','Purchasing Officer','2026-05-30 21:10:29'),(5,'Customs','Customs Officer','2026-05-30 21:10:29'),(6,'Technician','Maintenance Technician','2026-05-30 21:10:29');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `setting_value` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
INSERT INTO `settings` VALUES (1,'system_name','Customs Portal','2026-05-30 21:23:26','2026-05-30 21:23:26'),(2,'default_language','ar','2026-05-30 21:23:26','2026-05-30 21:23:26'),(3,'currency','KWD','2026-05-30 21:23:26','2026-05-30 21:23:26'),(4,'timezone','Asia/Kuwait','2026-05-30 21:23:26','2026-05-30 21:23:26');
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shipping_containers`
--

DROP TABLE IF EXISTS `shipping_containers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shipping_containers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `declaration_id` bigint NOT NULL,
  `container_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `seal_no` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `arrival_date` date DEFAULT NULL,
  `container_status` enum('in_transit','arrived','under_clearance','released') COLLATE utf8mb4_unicode_ci DEFAULT 'in_transit',
  PRIMARY KEY (`id`),
  KEY `idx_container_declaration` (`declaration_id`),
  CONSTRAINT `fk_container_declaration` FOREIGN KEY (`declaration_id`) REFERENCES `customs_declarations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shipping_containers`
--

LOCK TABLES `shipping_containers` WRITE;
/*!40000 ALTER TABLE `shipping_containers` DISABLE KEYS */;
/*!40000 ALTER TABLE `shipping_containers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shipping_documents`
--

DROP TABLE IF EXISTS `shipping_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shipping_documents` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `declaration_id` bigint NOT NULL,
  `document_type` enum('invoice','packing_list','certificate_origin','bill_of_lading','other') COLLATE utf8mb4_unicode_ci NOT NULL,
  `document_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_document_declaration` (`declaration_id`),
  CONSTRAINT `fk_document_declaration` FOREIGN KEY (`declaration_id`) REFERENCES `customs_declarations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shipping_documents`
--

LOCK TABLES `shipping_documents` WRITE;
/*!40000 ALTER TABLE `shipping_documents` DISABLE KEYS */;
/*!40000 ALTER TABLE `shipping_documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_issues`
--

DROP TABLE IF EXISTS `stock_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_issues` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `store_id` int NOT NULL,
  `qty` decimal(12,2) NOT NULL,
  `issued_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `issue_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_issues`
--

LOCK TABLES `stock_issues` WRITE;
/*!40000 ALTER TABLE `stock_issues` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_issues` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_transfer_items`
--

DROP TABLE IF EXISTS `stock_transfer_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_transfer_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `transfer_id` bigint NOT NULL,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `unit_cost` decimal(18,4) DEFAULT '0.0000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transfer_item` (`transfer_id`,`item_id`),
  KEY `idx_transfer_items_item` (`item_id`),
  CONSTRAINT `fk_transfer_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_transfer_items_transfer` FOREIGN KEY (`transfer_id`) REFERENCES `stock_transfers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_transfer_items`
--

LOCK TABLES `stock_transfer_items` WRITE;
/*!40000 ALTER TABLE `stock_transfer_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_transfer_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_transfers`
--

DROP TABLE IF EXISTS `stock_transfers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_transfers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `transfer_no` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `from_store_id` int NOT NULL,
  `to_store_id` int NOT NULL,
  `transfer_date` date NOT NULL,
  `status` enum('draft','approved','in_transit','received','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_by` int DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transfer_no` (`transfer_no`),
  KEY `fk_transfer_created_by` (`created_by`),
  KEY `fk_transfer_approved_by` (`approved_by`),
  KEY `idx_transfer_from_store` (`from_store_id`),
  KEY `idx_transfer_to_store` (`to_store_id`),
  KEY `idx_transfer_status` (`status`),
  CONSTRAINT `fk_transfer_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_transfer_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_transfer_from_store` FOREIGN KEY (`from_store_id`) REFERENCES `stores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_transfer_to_store` FOREIGN KEY (`to_store_id`) REFERENCES `stores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_transfers`
--

LOCK TABLES `stock_transfers` WRITE;
/*!40000 ALTER TABLE `stock_transfers` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_transfers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `store_items`
--

DROP TABLE IF EXISTS `store_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `store_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `store_id` int NOT NULL,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) DEFAULT '0.00',
  `reserved_quantity` decimal(18,2) DEFAULT '0.00',
  `average_cost` decimal(18,4) DEFAULT '0.0000',
  `last_movement_date` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_store_item` (`store_id`,`item_id`),
  KEY `idx_store_items_store` (`store_id`),
  KEY `idx_store_items_item` (`item_id`),
  CONSTRAINT `fk_store_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_store_items_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `store_items`
--

LOCK TABLES `store_items` WRITE;
/*!40000 ALTER TABLE `store_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `store_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `store_locations`
--

DROP TABLE IF EXISTS `store_locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `store_locations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `store_id` int NOT NULL,
  `location_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_store_locations_store` (`store_id`),
  CONSTRAINT `fk_store_locations_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `store_locations`
--

LOCK TABLES `store_locations` WRITE;
/*!40000 ALTER TABLE `store_locations` DISABLE KEYS */;
/*!40000 ALTER TABLE `store_locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stores`
--

DROP TABLE IF EXISTS `stores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `store_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `store_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `manager` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `store_code` (`store_code`),
  KEY `idx_stores_name` (`store_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stores`
--

LOCK TABLES `stores` WRITE;
/*!40000 ALTER TABLE `stores` DISABLE KEYS */;
/*!40000 ALTER TABLE `stores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `units`
--

DROP TABLE IF EXISTS `units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `units` (
  `id` int NOT NULL AUTO_INCREMENT,
  `unit_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unit_code` (`unit_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `units`
--

LOCK TABLES `units` WRITE;
/*!40000 ALTER TABLE `units` DISABLE KEYS */;
INSERT INTO `units` VALUES (1,'Piece','PCS','2026-05-30 21:16:14'),(2,'Kilogram','KG','2026-05-30 21:16:14'),(3,'Meter','M','2026-05-30 21:16:14'),(4,'Liter','LTR','2026-05-30 21:16:14'),(5,'Box','BOX','2026-05-30 21:16:14'),(6,'Pack','PACK','2026-05-30 21:16:14');
/*!40000 ALTER TABLE `units` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_permissions`
--

DROP TABLE IF EXISTS `user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_permissions` (
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  `allow_access` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`user_id`,`permission_id`),
  KEY `fk_user_permissions_permission` (`permission_id`),
  CONSTRAINT `fk_user_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_permissions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_permissions`
--

LOCK TABLES `user_permissions` WRITE;
/*!40000 ALTER TABLE `user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `full_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `language` enum('ar','en') COLLATE utf8mb4_unicode_ci DEFAULT 'ar',
  `status` enum('active','inactive','suspended') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `last_login_at` datetime DEFAULT NULL,
  `last_login_ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_users_role` (`role_id`),
  KEY `idx_users_status` (`status`),
  CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,1,'Administrator','admin','admin@local','scrypt:32768:8:1$LMjXffjadw3i8yx8$24adf3c9cb97d31b6906d058b7a7f427030b4d32b846b15d69c48698616b440adc9585c0e28348ecd3ba23788c0757d37e16137d2c4a2b5a78b6a3d75407a8fa',NULL,'ar','active',NULL,'2026-05-30 22:05:08','2026-05-31 10:02:46');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendor_contacts`
--

DROP TABLE IF EXISTS `vendor_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendor_contacts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vendor_id` int NOT NULL,
  `contact_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `position_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_vendor_contacts_vendor` (`vendor_id`),
  CONSTRAINT `fk_vendor_contacts_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendors` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendor_contacts`
--

LOCK TABLES `vendor_contacts` WRITE;
/*!40000 ALTER TABLE `vendor_contacts` DISABLE KEYS */;
/*!40000 ALTER TABLE `vendor_contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendors`
--

DROP TABLE IF EXISTS `vendors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendors` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `vendor_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tax_number` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `website` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vendor_code` (`vendor_code`),
  KEY `idx_vendors_name` (`vendor_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendors`
--

LOCK TABLES `vendors` WRITE;
/*!40000 ALTER TABLE `vendors` DISABLE KEYS */;
INSERT INTO `vendors` VALUES (1,'VND-001','Default Vendor',NULL,'+000000000',NULL,NULL,NULL,'active','2026-05-30 21:19:06','2026-05-30 21:19:06');
/*!40000 ALTER TABLE `vendors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `vw_current_stock`
--

DROP TABLE IF EXISTS `vw_current_stock`;
/*!50001 DROP VIEW IF EXISTS `vw_current_stock`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_current_stock` AS SELECT 
 1 AS `store_name`,
 1 AS `item_code`,
 1 AS `item_name_ar`,
 1 AS `quantity`,
 1 AS `average_cost`,
 1 AS `total_value`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_low_stock_items`
--

DROP TABLE IF EXISTS `vw_low_stock_items`;
/*!50001 DROP VIEW IF EXISTS `vw_low_stock_items`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_low_stock_items` AS SELECT 
 1 AS `item_code`,
 1 AS `item_name_ar`,
 1 AS `quantity`,
 1 AS `min_qty`,
 1 AS `store_name`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_purchase_summary`
--

DROP TABLE IF EXISTS `vw_purchase_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_purchase_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_purchase_summary` AS SELECT 
 1 AS `po_number`,
 1 AS `vendor_name`,
 1 AS `order_date`,
 1 AS `status`,
 1 AS `total_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `workshop_items`
--

DROP TABLE IF EXISTS `workshop_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workshop_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `quantity` decimal(18,2) NOT NULL,
  `status` enum('received','processing','finished','returned') COLLATE utf8mb4_unicode_ci DEFAULT 'received',
  `received_date` date DEFAULT NULL,
  `completed_date` date DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_workshop_item` (`item_id`),
  KEY `idx_workshop_status` (`status`),
  CONSTRAINT `fk_workshop_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workshop_items`
--

LOCK TABLES `workshop_items` WRITE;
/*!40000 ALTER TABLE `workshop_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `workshop_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `vw_current_stock`
--

/*!50001 DROP VIEW IF EXISTS `vw_current_stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_current_stock` AS select `s`.`store_name` AS `store_name`,`i`.`item_code` AS `item_code`,`i`.`item_name_ar` AS `item_name_ar`,`si`.`quantity` AS `quantity`,`si`.`average_cost` AS `average_cost`,(`si`.`quantity` * `si`.`average_cost`) AS `total_value` from ((`store_items` `si` join `stores` `s` on((`s`.`id` = `si`.`store_id`))) join `items` `i` on((`i`.`id` = `si`.`item_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_low_stock_items`
--

/*!50001 DROP VIEW IF EXISTS `vw_low_stock_items`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_low_stock_items` AS select `i`.`item_code` AS `item_code`,`i`.`item_name_ar` AS `item_name_ar`,`si`.`quantity` AS `quantity`,`i`.`min_qty` AS `min_qty`,`s`.`store_name` AS `store_name` from ((`store_items` `si` join `items` `i` on((`i`.`id` = `si`.`item_id`))) join `stores` `s` on((`s`.`id` = `si`.`store_id`))) where (`si`.`quantity` <= `i`.`min_qty`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_purchase_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_purchase_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_purchase_summary` AS select `po`.`po_number` AS `po_number`,`v`.`vendor_name` AS `vendor_name`,`po`.`order_date` AS `order_date`,`po`.`status` AS `status`,`po`.`total_amount` AS `total_amount` from (`purchase_orders` `po` join `vendors` `v` on((`v`.`id` = `po`.`vendor_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-01 21:52:41
