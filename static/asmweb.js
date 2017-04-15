function submitasm() {
    $.post('/assemble/', $('#asm').val(), function(data) {
        if (data['error']) {
            newerror = $("<div>").append($('<strong>', {text: data['error'][0] + ":"}));
            newerror.append(' ' + data['error'][1]);
            newerror.append('<br><strong>Instruction:</strong> ' + data['error'][2]);
            $('#error').html(newerror);
            $('#error').show().removeClass('hide');
            $('#noerror').fadeTo("slow", 0.4);
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
            $('#noerror').fadeTo("fast", 1.0);
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
    addsave($('#saveas').val(), $('#asm').val());
    updatesaves();
}
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
    $('#asm').val(saves[savename]);
    submitasm();
    return false;
});
$('#asm').on('input propertychange', function() {
    submitasm();
});
$(function() {
    updatesaves();
    // load the sample
    $.get('/sample.asm', function(data) {
        $('#asm').val(data);
        // assemble it
        submitasm();
    });
});
