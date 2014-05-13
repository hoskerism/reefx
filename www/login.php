<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?php

	require('functions.php');
	
	$_SESSION['debug'] = 'start: ' . print_r($_REQUEST, true);
	
	if ($_POST['username'] != '' && $_POST['password'] != '')
	{
		$_SESSION['debug'] .= 'logging in: ' . $_POST['username'] . ' / ' . $_POST['password'] . ' / ' . ($_POST['private'] == 'true');
		login($_POST['username'], $_POST['password'], $_POST['private'] == 'true');
	}

	if ($_SESSION['USERNAME'] != '')
	{
	  header('Location:/');
	}
	
?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>Reef X - Login</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>

<body>
	<?php //echo $_SESSION['debug']; ?>
  <form method="post">  
    <div class="data-heading" id="login-heading">
	  <span class="module-title">
        Login
      </span>
    </div>

    <div class="data-content" id="login-content">
      <span class="module-content">        
        <table>
          <tr>
            <td>Username</td>
            <td><input type="text" name="username" /></td>
          </tr>
          <tr>
            <td>Password</td>
            <td><input type="password" name="password" /></td>
          </tr>
          <tr>
            <td><input type="checkbox" name="private" value="true" />This is a Private Computer</td>
            <td align="right"><input type="submit" name="submit" value="submit" /></td>
          </tr>
        </table>
      </span>
    </div>
  </form>
</body>
</html>