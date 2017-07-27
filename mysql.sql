-- MySQL dump 10.13  Distrib 5.6.30, for debian-linux-gnu (x86_64)
--
-- RaiBlocks Telegram bot
-- @RaiWalletBot https://t.me/RaiWalletBot
-- 
-- Source code:
-- https://github.com/SergiySW/RaiWalletBot
-- 
-- Released under the BSD 3-Clause License
--
--
-- MySQL database structure dump
--

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `rai_black_list`
--

DROP TABLE IF EXISTS `rai_black_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_black_list` (
  `user_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot`
--

DROP TABLE IF EXISTS `rai_bot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `account` varchar(64) DEFAULT NULL,
  `frontier` varchar(64) DEFAULT NULL,
  `balance` bigint(15) unsigned NOT NULL DEFAULT '0',
  `send_destination` varchar(64) DEFAULT NULL,
  `send_amount` bigint(15) unsigned NOT NULL DEFAULT '0',
  `chat_id` int(11) unsigned NOT NULL,
  `username` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `username` (`username`),
  KEY `user_id` (`user_id`),
  KEY `account` (`account`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_access`
--

DROP TABLE IF EXISTS `rai_bot_access`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_access` (
  `user_id` int(10) unsigned NOT NULL,
  `datetime` int(11) unsigned NOT NULL DEFAULT '0',
  `message_id` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_extra`
--

DROP TABLE IF EXISTS `rai_bot_extra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_extra` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `extra_id` int(3) unsigned NOT NULL DEFAULT '1',
  `account` varchar(64) DEFAULT NULL,
  `frontier` varchar(64) DEFAULT NULL,
  `balance` bigint(15) unsigned NOT NULL DEFAULT '0',
  `send_from` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `account` (`account`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_hide_list`
--

DROP TABLE IF EXISTS `rai_bot_hide_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_hide_list` (
  `user_id` int(10) unsigned NOT NULL,
  `hide` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_language`
--

DROP TABLE IF EXISTS `rai_bot_language`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_language` (
  `user_id` int(10) unsigned NOT NULL,
  `language` varchar(2) NOT NULL DEFAULT 'en',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_passwords`
--

DROP TABLE IF EXISTS `rai_bot_passwords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_passwords` (
  `user_id` int(10) unsigned NOT NULL,
  `password` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_seeds`
--

DROP TABLE IF EXISTS `rai_bot_seeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_seeds` (
  `user_id` int(10) NOT NULL,
  `seed` char(16) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `seed` (`seed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_send_all`
--

DROP TABLE IF EXISTS `rai_bot_send_all`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_send_all` (
  `user_id` int(10) unsigned NOT NULL,
  `active` tinyint(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_bot_send_time`
--

DROP TABLE IF EXISTS `rai_bot_send_time`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_bot_send_time` (
  `user_id` int(10) unsigned NOT NULL,
  `datetime` int(11) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_frontiers`
--

DROP TABLE IF EXISTS `rai_frontiers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_frontiers` (
  `id` int(2) NOT NULL,
  `json` mediumtext NOT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
INSERT INTO `rai_frontiers` (`id`, `json`) VALUES
(1, '{}')
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_price`
--

DROP TABLE IF EXISTS `rai_price`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_price` (
  `id` int(3) unsigned NOT NULL AUTO_INCREMENT,
  `last_price` int(11) unsigned NOT NULL DEFAULT '0',
  `high_price` int(11) unsigned NOT NULL DEFAULT '0',
  `low_price` int(11) unsigned NOT NULL DEFAULT '0',
  `ask_price` int(11) unsigned NOT NULL DEFAULT '0',
  `bid_price` int(11) unsigned NOT NULL DEFAULT '0',
  `volume` bigint(18) unsigned NOT NULL DEFAULT '0',
  `btc_volume` bigint(18) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

--
-- Table structure for table `rai_price_high`
--

DROP TABLE IF EXISTS `rai_price_high`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_price_high` (
  `user_id` int(10) unsigned NOT NULL,
  `price` int(10) unsigned NOT NULL DEFAULT '100000000',
  `exchange` tinyint(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_price_low`
--

DROP TABLE IF EXISTS `rai_price_low`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_price_low` (
  `user_id` int(10) unsigned NOT NULL,
  `price` int(10) unsigned NOT NULL DEFAULT '1000',
  `exchange` tinyint(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rai_send_list`
--

DROP TABLE IF EXISTS `rai_send_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rai_send_list` (
  `id` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `text` text DEFAULT NOT NULL
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

