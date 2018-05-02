-- phpMyAdmin SQL Dump
-- version 3.4.11.1deb2+deb7u1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Oct 15, 2014 at 12:25 PM
-- Server version: 5.5.38
-- PHP Version: 5.4.4-14+deb7u12

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `aquamon`
--

-- --------------------------------------------------------

--
-- Table structure for table `action_log`
--

DROP TABLE IF EXISTS `action_log`;
CREATE TABLE IF NOT EXISTS `action_log` (
  `action_log_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(50) NOT NULL,
  `device` varchar(50) NOT NULL,
  `value` double NOT NULL,
  `message` text,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `time_stamp` decimal(14,3) NOT NULL,
  PRIMARY KEY (`action_log_id`),
  KEY `sensor` (`device`,`date`),
  KEY `module` (`module`),
  KEY `time_stamp` (`time_stamp`),
  KEY `date` (`date`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=13274 ;

-- --------------------------------------------------------

--
-- Table structure for table `config`
--

DROP TABLE IF EXISTS `config`;
CREATE TABLE IF NOT EXISTS `config` (
  `config_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(64) NOT NULL,
  `code` varchar(64) NOT NULL,
  `value` varchar(1024) NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_id`),
  KEY `module` (`module`,`code`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=3 ;

-- --------------------------------------------------------

--
-- Table structure for table `event_log`
--

DROP TABLE IF EXISTS `event_log`;
CREATE TABLE IF NOT EXISTS `event_log` (
  `event_log_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(50) NOT NULL,
  `level` int(11) NOT NULL,
  `code` varchar(64) NOT NULL,
  `message` varchar(16000) NOT NULL,
  `additional` text NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `time_stamp` decimal(14,3) NOT NULL,
  PRIMARY KEY (`event_log_id`),
  KEY `module` (`module`),
  KEY `time_stamp` (`time_stamp`),
  KEY `date` (`date`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=148184 ;

-- --------------------------------------------------------

--
-- Table structure for table `programs`
--

DROP TABLE IF EXISTS `programs`;
CREATE TABLE IF NOT EXISTS `programs` (
  `program_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(50) NOT NULL,
  `code` varchar(32) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `default_program` tinyint(1) NOT NULL,
  `relative_times` tinyint(1) NOT NULL,
  `repeat_program` tinyint(1) NOT NULL,
  `selected` tinyint(1) NOT NULL,
  `show_in_list` tinyint(1) NOT NULL DEFAULT '1',
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`program_id`),
  KEY `sensor` (`name`,`date`),
  KEY `module` (`module`),
  KEY `date` (`date`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=28 ;

-- --------------------------------------------------------

--
-- Table structure for table `program_actions`
--

DROP TABLE IF EXISTS `program_actions`;
CREATE TABLE IF NOT EXISTS `program_actions` (
  `program_action_id` int(11) NOT NULL AUTO_INCREMENT,
  `program_id` int(11) NOT NULL,
  `device` varchar(50) NOT NULL,
  `action_time` time NOT NULL,
  `value` tinyint(1) NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`program_action_id`),
  KEY `sensor` (`device`,`date`),
  KEY `module` (`program_id`),
  KEY `date` (`date`),
  KEY `program_id` (`program_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=98 ;

-- --------------------------------------------------------

--
-- Table structure for table `sensor_log`
--

DROP TABLE IF EXISTS `sensor_log`;
CREATE TABLE IF NOT EXISTS `sensor_log` (
  `sensor_log_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(50) NOT NULL,
  `sensor` varchar(50) NOT NULL,
  `value` double NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `time_stamp` decimal(14,3) NOT NULL,
  PRIMARY KEY (`sensor_log_id`),
  KEY `sensor` (`sensor`,`date`),
  KEY `module` (`module`),
  KEY `time_stamp` (`time_stamp`),
  KEY `date` (`date`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=207588 ;

-- --------------------------------------------------------

--
-- Table structure for table `status_log`
--

DROP TABLE IF EXISTS `status_log`;
CREATE TABLE IF NOT EXISTS `status_log` (
  `status_id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(50) NOT NULL,
  `status` tinyint(4) NOT NULL,
  `message` varchar(3000) DEFAULT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `time_stamp` decimal(14,3) NOT NULL,
  PRIMARY KEY (`status_id`),
  KEY `module` (`module`),
  KEY `time_stamp` (`time_stamp`),
  KEY `date` (`date`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=18566 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
