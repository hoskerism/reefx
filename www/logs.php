<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?php 
	require('functions.php');
	require_login();
	$worker = $_REQUEST['worker']; 
	$log_type = $_REQUEST['log_type'];
	
	$from = isset($_REQUEST['from']) && $_REQUEST['from'] != '' ? $_REQUEST['from'] : date('Y-m-d H:i:s', strtotime('-1 day'));
	$to = isset($_REQUEST['to']) && $_REQUEST['to'] != '' ? $_REQUEST['to'] : date('Y-m-d H:i:s', strtotime('now'));
	
	$page = isset($_REQUEST['page']) ? $_REQUEST['page'] : 1;
	$row_start = ($page - 1) * 100;
	$row_end = $page * 100;
?>

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reef X - Logs</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>

<body>
<a href="/">Home</a><br/>
<form name="logs">
	<span class="label">
  Log Type:&nbsp;
	<select name="log_type">
  	<option value="ALL" <?php if ($log_type == 'ALL') echo 'selected'; ?> >All</option>
    <option value="EVENTS" <?php if ($log_type == 'EVENTS') echo 'selected'; ?> >Events</option>
    <option value="STATUS" <?php if ($log_type == 'STATUS') echo 'selected'; ?> >Status</option>
    <option value="SENSORS" <?php if ($log_type == 'SENSORS') echo 'selected'; ?> >Sensors</option>
    <option value="ACTIONS" <?php if ($log_type == 'ACTIONS') echo 'selected'; ?> >Actions</option>
  </select>
  </span>
  <span class="label">
  Worker:&nbsp;
  <select name="worker">
  	<option value="ALL">All</option>
<?php 
	$workers = reefx_request('LIST_WORKERS');
	foreach ($workers['WORKER'] as $workerrow)
	{
		$selected = $workerrow['NAME'] == $worker ? "selected" : "";
		echo '<option value="' . $workerrow['NAME'] . '" ' . $selected . ' >' . $workerrow['FRIENDLY_NAME'] . '</option>';
	}
?>
  </select>
  </span>
  <span class="label">From:&nbsp;<input type="text" name="from" value="<?php echo $from; ?>" /></span>
  <span class="label">To:&nbsp;<input type="text" name="to" value="<?php echo $to; ?>" /></span>
  <input type="submit" value="Submit">
</form>
<?

$worker_clause = $worker == "ALL" ? "" : "AND module = '" . $worker ."' ";
$from_clause = "AND date >= '" . $from . "' ";
$to_clause = $to == "" ? "" : "AND date <= '" . $to . "' ";
$date_clause = $from_clause . $to_clause;

switch ($log_type)
{
	case "ALL":
		$sql = "
			SELECT 'action_log' as source, action_log_id as id, module, '' as level, device as item, 
				case value
					when 0 then 'OFF'
					when 1 then 'ON'
					else 'UNKNOWN'
				end as value,
				message, '' as additional, date, time_stamp
			FROM action_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "

			UNION
			
			SELECT 'event_log', event_log_id as id, module, 
					case level
						when 0 then 'DEBUG'
						when 1 then 'AUDIT'
						when 2 then 'INFO'
						when 3 then 'WARNING'
						when 4 then 'ALERT'
						when 5 then 'EXCEPTION'
						else 'UNKNOWN'
					end as level,
					code, '' as value, message, additional, date, time_stamp
			FROM event_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			
			UNION
			
			SELECT 'sensor_log', sensor_log_id, module, '', sensor, value, '', '', date, time_stamp
			FROM sensor_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			
			UNION
			
			SELECT 'status_log', status_id, module, 
					case status
						when 0 then 'OK'
						when 1 then 'WARNING'
						when 2 then 'ALERT'
						when 3 then 'CRITICAL'
						when 4 then 'UNDEFINED'
						else 'UNKNOWN'
					end as status, 
					'', '', message, '', date, time_stamp
			FROM status_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			
			ORDER BY time_stamp DESC 
			" . $limit_clause . " ";
		break;
		
	case 'EVENTS':
		$sql = "
			SELECT event_log_id as id, module, 
					case level
						when 0 then 'DEBUG'
						when 1 then 'AUDIT'
						when 2 then 'INFO'
						when 3 then 'WARNING'
						when 4 then 'ALERT'
						when 5 then 'EXCEPTION'
						else 'UNKNOWN'
					end as level,
					code, message, additional, date
			FROM event_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			order by event_log_id desc ";
			
		break;
		
	case 'STATUS':
		$sql = "
			SELECT status_id as id, module, 
					case status
						when 0 then 'OK'
						when 1 then 'WARNING'
						when 2 then 'ALERT'
						when 3 then 'CRITICAL'
						when 4 then 'UNDEFINED'
						else 'UNKNOWN'
					end as status, 
					message, date
			FROM status_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			order by status_id desc ";
			
		break;
		
	case "SENSORS":
		$sql = "
			SELECT sensor_log_id as id, module, sensor, value, date
			FROM sensor_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			order by sensor_log_id desc ";
			
		break;
		
	case "ACTIONS":
		$sql = "
			SELECT action_log_id as id, module, device as item, 
				case value
					when 0 then 'OFF'
					when 1 then 'ON'
					else 'UNKNOWN'
				end as value,
				message, date
			FROM action_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $worker_clause . "
			order by action_log_id desc ";
			
		break;
}
		
//echo "SQL: " . $sql . "<br/>";		

$logs_array = db_read($sql, $row_start, $row_end);

if (count($logs_array) == 0)
{
	if ($log_type != '') echo '0 rows returned<br/>';
}
else
{

	echo '<table>';
	echo '<tr><td align="center">';	
	split_array_results($page, $logs_array);
	echo '</td></tr>';
	echo '<tr><td>';
	
	echo '<table><tr>';
	foreach (array_keys($logs_array[0]) as $key)
	{
		if ($key != 'time_stamp')
		{
			echo '<td class="header">' . $key . '</td>';
		}
	}
	echo '</tr>';
	
	$i = 0;
	
	foreach ($logs_array as $log)
	{
		$i += 1;
		$rowstyle = $i % 2 == 0 ? "even" : "odd";
		echo '<tr>';
		foreach (array_keys($log) as $key)
		{
			if ($key != 'time_stamp')
			{
				echo '<td class="' . $rowstyle . '" >' . str_replace("\r\n", "<br/>", $log[$key]) . '</td>';
			}
		}
		echo '</tr>';
	}
	echo '</table>';
	
	echo '</td></tr>';
	echo '<tr><td align="center">';	
	split_array_results($page, $logs_array);
	echo '</td></tr>';
	echo '</table>';
}
?>
</body>
</html>