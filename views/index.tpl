<!DOCTYPE html>
<html>
<head>
  <title>{{name}}web</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous">
  <link rel="stylesheet" href="static/codemirror.css">
  <link rel="stylesheet" href="static/asmweb.css">
  <link rel="icon" type-"image/png" href="static/256asm_icon.png">
</head>
<body>
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-10 col-md-offset-1">
        <div class="page-header">
          <h1>
            {{name}}web
            <small>Paste or type {{name}} ISA code to see the {{name}} ISA assembler output.</small>
          </h1>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-6 col-lg-7">
        <h2>Assembly</h2>
        <div class="panel panel-default" id="cm_container">
        </div>
        <div class="row"><div class="col-md-10 col-md-offset-1">
            <h4>Save code (to browser's local storage)</h4>
            <div class="input-group">
              <input id='saveas' type="text" class="form-control" placeholder="Save as...">
              <span class="input-group-btn">
                <button id="savebutton" type="submit" class="btn btn-primary">Save</button>
              </span>
            </div>
            <div id='savebox'>
              <h4>Load saved code</h4>
              <div class='list-group' id='saves'></div>
            </div>
        </div></div>
      </div>
      <div class="col-md-6 col-lg-5">
        <h2>Machine Code</h2>
        <div id="info" class="hide"></div>
        <div id="error" class="alert alert-danger hide"></div>
        <div id="machine_code_panel">
          <div class="panel panel-default">
            <div class="panel-body">
              <div id="machine_code"></div>
            </div>
          </div>
          <h3>For Logisim</h3>
          <div class="row">
            <div class="col-sm-12">
              <div class="panel panel-default">
                <div class="panel-heading">
                  <button id="copyhigh" class="btn btn-primary btn-xs pull-right">Copy</button>
                  Machine Code
                </div>
                <div id="bin" class="panel-body"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <footer class="footer">
      <p>Download command line version: <a href="/dl/{{name}}2bin.zip">{{name}}2bin</a></p>
      <p>Source: <a href="https://github.com/liffiton/256asm">256asm on Github</a></p>
    </footer>
  </div>
<script
	src="https://code.jquery.com/jquery-3.4.1.min.js"
	integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo="
	crossorigin="anonymous"></script>
<script src="static/codemirror.js"></script>
<script src="static/mode_simple.js"></script>
<script type="text/JavaScript">
  // Create these here to be populated from the config, leaving the .js file static.
  var instruction_regex = /[{{ reg_prefix }}][0-9a-z]+\b/i;
  var register_regex = /(?:{{ '|'.join(instructions) }})\b/i;
</script>
<script src="static/asmweb.js"></script>
</body>
</html>
