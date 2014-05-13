<?php

	session_start();
	
	date_default_timezone_set('Australia/Sydney');
		
	function require_login()
	{		
		$_SESSION['debug'] .= "Require_login<br/>";
		if ($_SESSION['USERNAME'] == '')
		{
			// Do we have a cookie?
			$username = $_COOKIE['user'];
			$password = $_COOKIE['pass'];			
		  login($username, $password);
		}		
		
		if ($_SESSION['USERNAME'] == '')
		{
			header('Location:login.php');
			die();
		}
	}

	function login($username, $password, $private)
	{
		$sql = "SELECT COUNT(*) AS COUNT FROM config WHERE module = 'WEB' AND code = 'USER' AND value = " . db_str($username . "/" . $password);
		$_SESSION['debug'] .= "<br/>" . $sql . "<br/>";
		$count_array = db_read($sql);
		$_SESSION['debug'] .= print_r($count_array, true) . "<br/>";
		if ($count_array[0]['COUNT'] == 1)
		{
			$_SESSION['debug'] .= "Logged in.<br/>";
			$_SESSION['USERNAME'] = $username;
			
			if ($private)
			{
				$expiry = time() + (86400 * 90); // 86400 = 1 day
				setcookie('user', $username, $expiry); 
				setcookie('pass', $password, $expiry);
			}
			
			return true;
		}
		
		return false;
	}
	
	function draw_status_icon_small($status, $message)
	{
		echo '<img src="images/' . get_status_icon($status) . '" width="21" height="16" id="status_icon" alt="' . $message . '" title="' . $message. '" border="0">';
	}

	function get_status_icon($status)
	{
		switch ($status)
		{
			case '0':
				$image = 'status_ok.png';
				break;
			case '1':
				$image = 'status_warning.png';
				break;
			case '2':
				$image = 'status_alert.png';
				break;
			case '4':
				$image = 'status_undefined.png';
				break;
			default:
				$image = 'status_critical.png';
				break;
		}
		
		return $image;
	}

	// TODO: Remove
	function get_latest_sensor_log($sensor)
	{
		$readings = db_read("SELECT value FROM sensor_log WHERE sensor = '" . $sensor . "' ORDER BY sensor_log_id DESC", 0, 1);
		return $readings[0]['value'];
	}

	function db_read($sql, $start_row = 0, $limit = 100)
	{
		// Create connection
		$con=db_connect();

		// Check connection
		if (mysqli_connect_errno())
		{
			throw new Exception("Failed to connect to MySQL: " . mysqli_connect_error());
		}

		$resultset = mysqli_query($con, $sql . ' LIMIT ' . $start_row . ', ' . $limit);
		
		while($row = mysqli_fetch_array($resultset, MYSQLI_ASSOC))
		{
			$result[] = $row;
		}

		mysqli_close($con);
		
		return $result;
	}

	function db_connect()
	{
		return mysqli_connect("localhost", "aquamon", "P6BqcCLSGEKL9uzZ", "aquamon");
	}

	function db_str($string)
	{
		return "'" . str_replace("'", "''", $string) . "'";
	}
	
	function reefx_request($requestType, $parameters, $verbose)
	{
		//if ($verbose) echo 'Translating request to json<br/>';
		
		$array = array();
		$array['CODE'] = $requestType;
		$array['CALLER'] = 'WEB';
		$array['IP_ADDRESS'] = $_SERVER['REMOTE_ADDR'];
		$array['USERNAME'] = $_SESSION['USERNAME'];
		
		foreach ($parameters as $key => $value)
		{
			$array[$key] = $value;
		}
		
		$json = json_encode($array);
		
		//if ($verbose) echo $json . '<br/>';
		
		return socket_request($json . '<<EOF>>', $verbose);
	}
	 
	function socket_request($request, $verbose=false)
	{
		try
		{
		$address = 'raspberrypi';
		$service_port = 58394;
		
		if ($verbose) echo date("D, j M Y H:i:s") . '<br/>';
		
		$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
		if ($socket === false) {
			$message = "socket_create() failed: reason: " . socket_strerror(socket_last_error());
			if ($verbose) echo $message . "<br/>";
			throw new Exception($message);
		}
		
		if ($verbose) echo "Connecting...";
		$result = socket_connect($socket, $address, $service_port);
		if ($result === false) {
			$message = "socket_connect() failed.<br/>Reason: ($result) " . socket_strerror(socket_last_error($socket));
			if ($verbose) echo $message . "<br/>";
			throw new Exception($message);
		} else {
			if ($verbose) echo "OK.<br/>";
		}
		
		$in = $request;
		$out = '';
		
		if ($verbose) echo "Sending request...";
		socket_write($socket, $in, strlen($in));
		if ($verbose) echo "OK.<br/>";
		
		if ($verbose) echo "Reading response...";
		$buf = '';
		while ($out = socket_read($socket, 2048)) {
				$buf .= $out;
		}
		if ($verbose) echo "OK.<br/>";
		
		//if ($verbose) echo $buf . '<br/>';
		
		if ($verbose) echo "Closing socket...";
		socket_close($socket);
		if ($verbose) echo "OK.<br/>";
		
		if ($verbose) echo 'Parsing response...';
		$array = json_decode ($buf, true);
		if ($verbose) echo "OK.<br/>";
		
		//if ($verbose) echo print_r($array, true) . '<br/>';
		
		return $array;
		}
		catch (Exception $e) {
			$message = $e->getMessage();
			echo 'Caught exception: ',  $message, "<br/>";
		}
	}

	function split_array_results($page, $array)
	{
		if ($page > 1)
		{
			$_REQUEST['page'] = $page - 1;
			echo '<a href="logs.php?' . array_to_url($_REQUEST) . '" >&lt;=</a>';
		}
		
		if ($page > 1 || count($array) >= 100)
		{
			echo "&nbsp;page&nbsp;";
		}
		
		if (count($array) >= 100)
		{
			$_REQUEST['page'] = $page + 1;
			echo '<a href="logs.php?' . array_to_url($_REQUEST) . '" >=&gt;</a>';
		}
	}

	function array_to_url($arr)
	{
		$result = "";
		$separator = "";
		
		foreach(array_keys($arr) as $key)
		{
			$result .= $separator . urlencode($key) . '=' . urlencode($arr[$key]);
			$separator = "&";
		}
		
		return $result;
	}

?>