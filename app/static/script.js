$(document).ready(function(){
    $("button").click(function () {
        $.getJSON("/dicomconnect/find", function (data) {
            alert(data.data[0].PatientName);
        });
    });
});
