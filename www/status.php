<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?php
	require('functions.php');
	require_login();
?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>Reef X Status</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
<?php
try
{
	$status_array = reefx_request("WEB_STATUS_REQUEST", '', true);
	
	$status = $status_array['STATUS'];
	$code = $status_array['VALUE'];
	$message = $status_array['MESSAGE'];
	$image = get_status_icon($status);
	
}
catch (Exception $e) {
  $message = $e->getMessage();
	$image = 'status_critical.png';
	echo 'Caught exception: ',  $message, "<br/>";
}

echo '<a href="http://www.hoskerism.com:8080"><img src="http://www.hoskerism.com:8080/images/' . $image . '" width="98" height="77" id="status_icon" alt="' . $message . '" title="' . $message . '" border="0"></a><br/>';

echo 'Status: ' . $code . "<br/>";
echo str_replace("\n", '<br/>', $message);
?>
</body>
</html>