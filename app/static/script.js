$(document).ready(function(){

    let query_results = {};

    $("button").click(function () {
        $.getJSON("/dicomconnect/find", function (data) {
            alert(data.data[0].PatientName);
        });
    });

    $('#config_form').on('submit',function (e) {
        $.ajax({
            type: 'post',
            url: '/dicomconnect/update_configuration',
            data: $('#config_form').serialize(),
            success: function (q) {
                document.getElementById("configuration").innerHTML= q;
            }});
        e.preventDefault();
     });

    $('#upload_form').on('submit', function (e) {
        var form = $('#upload_form')[0];
        var formData = new FormData(form);
        console.log(formData);
        $.ajax({
            type: 'post',
            url: '/dicomconnect/_query',
            data: formData,
            contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
            processData: false, // NEEDED, DON'T OMIT THIS
            success: function (q) {
                document.getElementById("query_preview").innerHTML= make_row_header_table(q);
            }
        });
        e.preventDefault();
    });

    $('#echo_button').click(function () {
        $.get('/dicomconnect/_echo', function (e) {
            alert(e)
        });
    });

    $('#find_button').click(function () {
        query_results['find'] = run_query('find');
    });

    $(".download_button").on('click', function () {
        let query_type = $(this).attr("query-type");
        let filename = query_type + '_' + String($.now());
        console.log(query_type, filename)
        if (query_type in query_results) {
            $.ajax({
                type: 'post',
                url: '/dicomconnect/_save_json',
                contentType: 'application/json',
                data: JSON.stringify(query_results[query_type]),
                success: function (q) {
                    alert(q)
                },
                headers: {
                    'filename': filename
                }
            });
        } else {
            alert('No results for query type: ' + query_type);
            console.log('No results for query type: ' + query_type);
        }
    });

    $('#move_button').click(function () {
        run_query('move');
    });

    $('#store_button').click(function () {
        $.get('/dicomconnect/_store', function (data) {
            $('#store_status').html(data)
        });
    });

    $.getJSON('/dicomconnect/_query', function (data) {
            $('#query_preview').html(make_row_header_table(data))
    });

});

function run_query(query_type){

    let query_types = ['find', 'move'];
    var query_results = [];
    console.assert(query_types.includes(query_type), {query_type: query_type, error: 'non valid query type'} )

    $.getJSON('/dicomconnect/_query', function (queries) {
        var query_length = queries.length
        var i = 0

        $("#query_progress").attr('max', query_length)
        run_next_query()

        function run_next_query() {
            var query_response;
            if(!queries[i]) {
                return
            }
            $.ajax({
                type: 'post',
                url: '/dicomconnect/_' + query_type,
                contentType: 'application/json',
                // async: false,
                data: JSON.stringify(queries[i]),
                success: function (data) {
                    query_response = data;
                }
            }).done(function () {
                query_results.push({
                    "query_id": i,
                    "query": queries[i],
                    "query_response": query_response
                });

                $.each(query_response['data'], function (i, data_element) {
                    tabulate(data_element, "#query_results_table");
                });
                $.each(query_response['status'], function (i, data_element) {
                    console.log(data_element)
                    tabulate(data_element, "#query_status_table");
                });

                i++;

                $("#query_progress").val(i)

                run_next_query();
            })
        }
    })
    return query_results
};


function tabulate(single_dict, output_location){
    if ($(output_location).has('table').length == 0 ) {
        let html_string = '<table><thead><tr>';
        $.each(single_dict, function (key, val) {
            html_string += '<th>'+ key +'</th>';
        });
        html_string += '</tr></thead><tbody></tbody></table>';
        $(output_location).html(html_string)
    }

    let html_string = '<tr>';
    $(output_location + " table thead tr th").each(function (idx, val) {
        if (val.innerHTML in single_dict){
            html_string += '<td>'+ single_dict[val.innerHTML] +'</td>';
        } else {
            html_string += '<td></td>';
        }
        // could check here that no new fields are added, compare two lists
    });
    html_string += '</tr>';
    $(output_location + " table thead tr:last").after(html_string);
}


function make_table_header_row(single_dict) {
    let html_string = '';
    html_string += '<tr>';
    $.each(single_dict, function (key, val) {
        html_string += '<th>'+ key +'</th>';
    });
    html_string += '</tr>';
    return html_string;
}
function make_table_row(single_dict) {
    let html_string = '';
    html_string += '<tr>';
    $.each(single_dict, function (key, val) {
        html_string += '<td>'+ val +'</td>';
    });
    html_string += '</tr>';
    return html_string;
}

function make_row_header_table(json_data) {
    var html_string = '';
    if (json_data) {
        html_string += '<table>';

        html_string += '<tr>';
        $.each(json_data[0], function (key, value) {
            html_string += '<th>'+ key +'</th>';
        });
        html_string += '</tr>';


        $.each(json_data, function (index, value) {
            html_string += '<tr>';
            $.each(value, function (k, v) {
                html_string += '<td>'+v+'</td>';
            });
            html_string += '</tr>';
        });


        html_string += '</table>';

    } else {
        html_string += '<p> No table data. </p>';
    };
    return html_string;
};