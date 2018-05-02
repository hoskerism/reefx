<html>
<head>
<?php
	require('functions.php');
	require_login();
?>
<script type="text/javascript"
  src="js/dygraph-combined.js"></script>
</head>
<body>
<form>

<?php
	$range = isset($_REQUEST['range']) ? $_REQUEST['range'] : 1;
	$sensor = $_REQUEST['sensor'];
	
	$sensor_clause = "AND sensor = '" . $sensor . "' ";
	$date_clause = $range == 'ALL' ? '' : 'AND date >= ADDDATE(CURDATE(), ' . -$range . ') ';

	$sql = "
			SELECT date, value
			FROM sensor_log
			WHERE 1 = 1
			" . $date_clause . "
			" . $sensor_clause . "
			order by date";
	
	echo $sql;
	
	$sensor_array = db_read($sql, 0, 100000);
	//echo print_r($sensor_array, true);
?>

<div id="graphdiv"></div>
<script type="text/javascript">
  g = new Dygraph(

    // containing div
    document.getElementById("graphdiv"),

    // CSV or path to a CSV file.
    "Date,Temperature\n" +
<?php
	$first_row = true;
	foreach ($sensor_array as $log)
	{
		if ($first_row) 
		{
			$first_row = false;
		}
		else
		{
			echo '+';
		}
		
		echo '"' . $log['date'] . ',' . $log['value'] . '\\n"';
	}
?>

  );
</script>

<br/>
<input type="radio" name="range" value="1" <?php if ($range==1) echo 'checked'; ?>>1 day
<input type="radio" name="range" value="7" <?php if ($range==7) echo 'checked'; ?>>1 week
<input type="radio" name="range" value="30" <?php if ($range==30) echo 'checked'; ?>>1 month
<input type="radio" name="range" value="365" <?php if ($range==365) echo 'checked'; ?>>1 year
<input type="radio" name="range" value="ALL" <?php if ($range=='ALL') echo 'checked'; ?>>All
<input type="hidden" name="sensor" value="<?php echo $sensor; ?>">
<input type="submit" value="submit">
</form>
</body>
</html>