-- Host: localhost
-- Generation Time: May 10, 2018 at 10:31 AM
-- Server version: 10.1.26-MariaDB-0+deb9u1
-- PHP Version: 5.6.33-0+deb8u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `bernard`
--
CREATE DATABASE IF NOT EXISTS `bernard` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `bernard`;

-- --------------------------------------------------------

--
-- Table structure for table `auditing_blacklisted_domains`
--

CREATE TABLE IF NOT EXISTS `auditing_blacklisted_domains` (
  `domain` varchar(127) NOT NULL,
  `action` text NOT NULL,
  `added_by` bigint(20) NOT NULL,
  `added_when` double NOT NULL,
  `hits` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bans_retroactive`
--

CREATE TABLE IF NOT EXISTS `bans_retroactive` (
  `id` bigint(20) NOT NULL,
  `name` text NOT NULL,
  `reason` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `crypto`
--

CREATE TABLE IF NOT EXISTS `crypto` (
  `priority` int(11) NOT NULL,
  `exchange` text NOT NULL,
  `ticker` text NOT NULL,
  `currency` text NOT NULL,
  `uniq` varchar(24) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `crypto_cmc`
--

CREATE TABLE IF NOT EXISTS `crypto_cmc` (
  `ticker` varchar(24) NOT NULL,
  `id` text NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `crypto_lazy`
--

CREATE TABLE IF NOT EXISTS `crypto_lazy` (
  `ticker` text NOT NULL,
  `alias` varchar(24) NOT NULL,
  `added` double NOT NULL,
  `issued` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `journal_events`
--

CREATE TABLE IF NOT EXISTS `journal_events` (
  `jobid` mediumint(9) NOT NULL,
  `module` text NOT NULL,
  `event` bigint(20) DEFAULT NULL,
  `time` double NOT NULL,
  `userid` bigint(20) NOT NULL,
  `eventid` bigint(20) DEFAULT NULL,
  `contents` text NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=115 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `journal_jobs`
--

CREATE TABLE IF NOT EXISTS `journal_jobs` (
  `jobid` mediumint(9) NOT NULL,
  `module` text,
  `job` text,
  `time` double NOT NULL,
  `runtime` double NOT NULL,
  `result` text
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `journal_regulators`
--

CREATE TABLE IF NOT EXISTS `journal_regulators` (
  `id_invoker` bigint(20) NOT NULL,
  `id_targeted` bigint(20) NOT NULL,
  `id_message` text NOT NULL,
  `action` text NOT NULL,
  `time` int(11) NOT NULL,
  `event` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `subscribers`
--

CREATE TABLE IF NOT EXISTS `subscribers` (
  `userid` bigint(20) NOT NULL,
  `roleid` bigint(20) NOT NULL,
  `tier` text NOT NULL,
  `last_updated` double NOT NULL,
  `expires_epoch` double NOT NULL,
  `expires_day` smallint(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `auditing_blacklisted_domains`
--
ALTER TABLE `auditing_blacklisted_domains`
  ADD UNIQUE KEY `domain` (`domain`), ADD UNIQUE KEY `domain_2` (`domain`);

--
-- Indexes for table `bans_retroactive`
--
ALTER TABLE `bans_retroactive`
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `crypto`
--
ALTER TABLE `crypto`
  ADD UNIQUE KEY `uniq` (`uniq`);

--
-- Indexes for table `crypto_cmc`
--
ALTER TABLE `crypto_cmc`
  ADD UNIQUE KEY `ticker` (`ticker`);

--
-- Indexes for table `crypto_lazy`
--
ALTER TABLE `crypto_lazy`
  ADD UNIQUE KEY `alias` (`alias`);

--
-- Indexes for table `journal_events`
--
ALTER TABLE `journal_events`
  ADD PRIMARY KEY (`jobid`), ADD UNIQUE KEY `jobid` (`jobid`), ADD UNIQUE KEY `eventid` (`eventid`);

--
-- Indexes for table `journal_jobs`
--
ALTER TABLE `journal_jobs`
  ADD PRIMARY KEY (`jobid`), ADD UNIQUE KEY `jobid` (`jobid`);

--
-- Indexes for table `journal_regulators`
--
ALTER TABLE `journal_regulators`
  ADD PRIMARY KEY (`id_invoker`);

--
-- Indexes for table `subscribers`
--
ALTER TABLE `subscribers`
  ADD UNIQUE KEY `userid` (`userid`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `journal_events`
--
ALTER TABLE `journal_events`
  MODIFY `jobid` mediumint(9) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=1;
--
-- AUTO_INCREMENT for table `journal_jobs`
--
ALTER TABLE `journal_jobs`
  MODIFY `jobid` mediumint(9) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=1;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
