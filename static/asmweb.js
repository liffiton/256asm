var cm = null;
var cur_mark = null;

function submitasm() {
    $.post('/assemble/', cm.getValue(), function(data) {
        if (data['error']) {
            var err = data['error'];
            var newerror = $("<div>").append($('<strong>', {text: err['msg'] + ":"}));
            newerror.append(' ' + err['data']);
            newerror.append('<br><strong>Line ' + err['lineno'] + ': </strong>' + err['inst']);
            cur_mark = cm.markText(
                {line:err['lineno']-1, ch:0},
                {line:err['lineno'], ch:0},
                {className: 'cm-error'}
            );
            $('#error').html(newerror);
            $('#error').show().removeClass('hide');
            $('#machine_code_panel').addClass("dim");
        }
        else {
            if (data['messages'].length) {
                $('#info').show().removeClass('hide');
                $('#info').empty();
                data['messages'].forEach(function(msg) {
                    newinfo = $("<div>", {class: 'alert alert-info'});
                    newinfo.append($('<strong>', {text: msg[0] + ":"}));
                    newinfo.append(' ' + msg[1]);
                    $('#info').append(newinfo);
                });
            }
            else {
                $('#info').hide();
            }
            $('#machine_code').html(data['code']);
            $('#upper').html(data['upper']);
            $('#lower').html(data['lower']);
            $('#bin').html(data['bin']);
            $('#machine_code_panel').removeClass("dim");
            $('#error').hide();
        }
    });
}

function getsaves() {
    if (localStorage.getItem('saves') === null) {
        return {};
    }
    else {
        return JSON.parse(localStorage.getItem('saves'));
    }
}

function addsave(name, text) {
    saves = getsaves();
    saves[name] = text;
    localStorage.setItem('saves', JSON.stringify(saves));
}

function delsave(name) {
    saves = getsaves();
    delete saves[toremove];
    localStorage.setItem('saves', JSON.stringify(saves));
}

function updatesaves() {
    saves = getsaves();
    if (!$.isEmptyObject(saves)) {
        $('#saves').empty();
        for (savename in saves) {
            newitem = $('<div>', {class: 'input-group list-group-item'});
            newitem.append(
                $('<a>', {text: savename, href:'#', class: 'saveopt'})
            );
            newitem.append(
                $('<button>', {class: 'delbutton btn btn-default btn-xs pull-right'})
                .append($('<span>', {class: 'glyphicon glyphicon-remove', style: 'color: darkred'}))
            );
            $('#saves').append(newitem);
        }
        $('#savebox').show();
    }
    else {
        $('#savebox').hide();
    }
}

function dosave() {
    addsave($('#saveas').val(), cm.getValue());
    updatesaves();
}

function docopy(ev) {
    var contents = $(ev.target).closest(".panel").find(".panel-body")[0].textContent;

    // Copy to clipboard.  Thanks to https://stackoverflow.com/a/42416105
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px;";
    tempInput.value = contents;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);

    // Update button to indicate copy was successful
    $(ev.target)
      .removeClass("btn-primary")
      .addClass("btn-success")
      .text("Copied to clipboard");

    // Reset after 5 seconds
    setTimeout(function() {
        $(ev.target)
            .removeClass("btn-success")
            .addClass("btn-primary")
            .text("Copy");
    }, 5000);
}

function setupHandlers() {
    $('#savebutton').click(dosave);
    $('#saveas').keydown(function(e) {
        if (e.keyCode == 13) {  // 13 = enter
            dosave();
        }
    });
    $('#saves').on('click', '.delbutton', function(event) {
        toremove = this.previousSibling.innerHTML;  // hack!  Oh well.  :)
        delsave(toremove);
        updatesaves();
        return false;  // don't let anyone else (below) handle this.
    });
    $('#saves').on('click', '.saveopt', function(event) {
        savename = this.innerHTML;
        saves = getsaves();
        cm.setValue(saves[savename]);
        return false;
    });
    $('.copy_button').click(docopy);
    cm.on('change', function() {
        // Triggered by setValue() as well as input events.
        if (cur_mark) {
            cur_mark.clear();
            cur_mark = null;
        }
        submitasm();
    });
}

function setupCodeMirror() {
    // Simple mode documentation: https://codemirror.net/demo/simplemode.html
    CodeMirror.defineSimpleMode("256asm", {
        start: [
            // "sol" = match at start of line only
            {token: "label",       regex: /[\s]*[a-z][\w]+\:/i, sol: true, indent: true},
            {token: "instruction", regex: instruction_regex}, // /(?:add|addi|sub|light|copy|zj)\b/i},
            {token: "register",    regex: register_regex}, // /\$[0-9a-z]+/i},
            {token: "number",      regex: /(?:0x|0b)[a-f\d]+|[-+]?(?:\.\d+|\d+\.?\d*)\b/i},
            {token: "comment",     regex: /#.*/},
            {token: "target",      regex: /[a-z][\w]*/i},
            // simple way to catch a bunch of junk and highlight it...
            {token: "error",       regex: /[\S]+/},
        ],
        comment: [],
        meta: {
            lineComment: "#"
        }
    });

    var cm = CodeMirror(
        document.getElementById("cm_container"),
        {
            lineNumbers: true,
            lineWrapping: true,
            scrollbarStyle: 'native',
            theme: 'asmweb',
            // expand tabs
            extraKeys: {
                Tab: function(cm) {
                    var spaces = Array(cm.getOption("indentUnit") + 1).join(" ");
                    cm.replaceSelection(spaces);
                }
            }
        }
    );
    return cm;
}

$(function() {
    cm = setupCodeMirror();
    setupHandlers();
    updatesaves();
    // load the sample
    $.get(samplefile, function(data) {
        cm.setValue(data);
    });
});
