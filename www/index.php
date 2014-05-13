<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?php 
	require('functions.php');
	require_login();
	$module = $_REQUEST['module']; // This is the worker
	
	if ($_REQUEST['program_change'])
	{
		reefx_request('PROGRAM_REQUEST', array("VALUE" => $_REQUEST['program'], "WORKER" => $_REQUEST['worker']));
		sleep(2);
	}
	
	try
	{
		$status_array = reefx_request("WEB_STATUS_REQUEST");
		
		$status = $status_array['STATUS'];
		$code = $status_array['VALUE'];
		$message = $status_array['MESSAGE'];
		$image = get_status_icon($status);
	}
	catch (Exception $e) {
		$message = $e->getMessage();
		$image = 'status_critical.png';
		$error = 'Caught exception: ' .  $message . "<br/>";
	}
?>

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reef X</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
  <link rel="icon" type="image/png" href="http://www.hoskerism.com:8080/images/<?php echo $image; ?>">
</head>

<body>


<?php if ($error != "") echo '<div style="color:red">' . $error . '</div>'; ?>

<div class="data-content" id="status-indicator">
	<ul class="full-width">
  	<li class="centered">
    	<a href="/">
<?php echo '<img src="http://www.hoskerism.com:8080/images/' . $image . '" width="98" height="77" id="status_icon" alt="' . $message . '" title="' . $message. '" border="0"><br/>'; ?>
			</a>
		</li>
  </ul>
</div>

<?php 
	$workers = reefx_request('LIST_WORKERS');
	
	foreach ($workers['WORKER'] as $worker)
	{
?>
<div class="data-heading" id="<?php echo $worker['NAME']; ?>">
	<ul class="full-width">
  	<li>
<?php
		echo '<a href="/?module=' . $worker['NAME'] . '">'; // . '#' . $worker['NAME'] . '">'; NB: I had to disable this as it lead to the browser not refreshing when I re-clicked the link.
		draw_status_icon_small($worker['STATUS'], $message); 
		echo '&nbsp;' . $worker['FRIENDLY_NAME'] . '</a>';
?>
		</li>
  </ul>
</div>
<?php
		if ($module == $worker['NAME'] || ($module == '' && $worker['STATUS'] > 0))
		{
			$capabilities = reefx_request('CAPABILITIES_REQUEST', array("WORKER" => $worker['NAME']));
			//print_r($capabilities);
?>
<div class="separator">&nbsp;</div>
<div class="data-heading2">
	<ul class="full-width">
  	<li>Status: <?php echo $worker['STATUS_CODE']; ?></li>
  </ul>
</div>
  	
<?php 
	if ($worker['MESSAGE'] != $worker['STATUS_CODE']) 
	{
		echo '<div class="data-content2">';
		echo '<ul class="full-width">';
  	echo '<li>' . str_replace("\r\n", "<br/>", $worker['MESSAGE']) . '</li>';
  	echo '</ul>';
		echo '</div>';
	}

	if (!empty($capabilities['INFORMATION']))
	{
		echo '<div class="data-heading2">Information</div>';
		echo '<div class="data-content2">';	
		echo '<ul class="columnar">';
		
		foreach ($capabilities['INFORMATION'] as $reading)
		{
			echo '<li>' . $reading['NAME'] . ": " . $reading['VALUE'] . '</li>';
		}
		
		echo '</ul>';
		echo '</div>';
	}
	
	if (!empty($capabilities['SENSOR_READINGS']))
	{
		echo '<div class="data-heading2">Parameters</div>';
		echo '<div class="data-content2">';	
		echo '<ul class="columnar">';
		
		foreach ($capabilities['SENSOR_READINGS'] as $reading)
		{
			echo '<li>' . $reading['FRIENDLY_NAME'] . ": " . $reading['FRIENDLY_VALUE'] . '</li>';
		}
		
		echo '</ul>';
		echo '</div>';
	}
	
	if (!empty($capabilities['DEVICE_STATUSES']))
	{
  	echo '<div class="data-heading2">Devices</div>';
		echo '<div class="data-content2">';	
		echo '<ul class="columnar">';	
		foreach ($capabilities['DEVICE_STATUSES'] as $device)
		{
			if ($device['VALUE'] == 1)
			{
				$image = 'images/device_on.png';
				$image_alt = "ON";
			}
			else
			{
				$image = 'images/device_off.png';
				$image_alt = "OFF";
			}
		
			echo '<li><img src="' . $image . '" alt="' . $image_alt . '" title="' . $image_alt . '" width="12px" height="12px" />&nbsp;' . $device['FRIENDLY_NAME'] . '</li>';
		}
		
		echo '</ul>';
		echo '</div>';
	}
	
	if (!empty($capabilities['PROGRAMS']))
	{
  	echo '<div class="data-heading2">Program</div>';
		echo '<div class="data-content2">';	
		echo '<form method="post" name="programs_form">';
		echo '<input type="hidden" name="worker" value="' . $worker['NAME'] . '" />';
		echo '<input type="hidden" name="program_change" value="true" />';
		echo '<select name="program" onchange=\'this.form.submit()\'>';
		foreach ($capabilities['PROGRAMS'] as $program)
		{
			$selected = $program['running'] == 1 ? 'selected' : '';
			echo '<option value="' . $program['code'] . '" ' . $selected . ' >' . $program['name'] . '</option>';
		}
		
		echo '</select>';
		echo '<noscript><input type="submit" value="Submit"></noscript>';
		echo '</form>';
		echo '</div>';
	}
?>
	</span>
</div>
<?php
		}
	}
?>
    <div class="data-heading" id="Logs">
      <ul class="full-width">
        <li>
          <a href="/logs.php" >
          <!--draw_status_icon_small($worker['STATUS'], $message); -->
          Logs
        </li>
      </ul>
    </div>
<div class="separator">&nbsp;</div>
</body>
</html>