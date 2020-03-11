// Client-side variables

let query_results = {};
let configuration = {};
let query_file = {};

$(document).ready(function(){

    $('#config_form').on('submit',function (e) {
        e.preventDefault();
        configuration = getFormData($("#config_form"));
        let reference = "#config_form label";
        let target = "#config_form_results_table";
        make_config_table(configuration, reference, target);
     });

    $('#upload_form').on('submit', function (e) {
        e.preventDefault();
        var form = $('#upload_form')[0];
        var formData = new FormData(form);
        $.ajax({
            type: 'post',
            url: '/dicomconnect/_query_load',
            data: formData,
            contentType: false,
            processData: false,
            success: function (q) {
                $("#query_preview").empty();
                $.each(q, function (key, val) {
                    tabulate(val, "#query_preview");
                })
                query_file = q;
            }
        });
    });

    $('#echo_button').on('click', function () {
        $.get('/dicomconnect/_echo', configuration, function (response) {
            alert(response);
        });
    });

    $('#find_button').on('click', function () {
        $("#find_progress").val(0)
        query_results['find'] = run_query('find');
    });

    $('#find_download').on('click', function () {
        let filename = 'find_' + $.now().toString();
        save_json(query_results['find'], 'qry', filename);
    });

    $('#move_button').on('click', function () {
        $.get('/dicomconnect/_store_status', function (data) {
            if (!data['store_status']) {
                alert('error: store not running, but required for move');
            } else {
                $("#move_progress").val(0)
                query_results['move'] = run_query('move');
            }
        });
    });

    $('#move_download').on('click', function () {
        let filename = 'move_' + $.now().toString();
        save_json(query_results['move'], 'qry', filename);
    });

    $('#store_button').on('click', function () {
        $.get('/dicomconnect/_store', configuration,function (data) {
            set_store_status(data['store_status'], '#store_button')
        });
    });

    $(".overview-item-header").on('click', function () {
        $symbol = $(".expand-symbol", this);
        $content = $(this).next();
        $content.slideToggle(500, function () {
            $symbol.text(function () {
                return $content.is(":visible") ? "\u002D" : "\u002B";
            });
    });

});

    // must check if store is running on page entry;

    $.get('/dicomconnect/_store_status', function (data) {
        set_store_status(data['store_status'], '#store_button')
    })

    $('#convert_button').on('click', function () {
        let move_qry = find_to_move(query_results['find']);
        if (move_qry) {
            $("#query_preview").empty();
            $.each(move_qry, function (key, val) {
                tabulate(val, "#query_preview");
            });
            query_file = move_qry;
            let filename = 'find_2_move_' + $.now().toString();
            save_json(query_file, 'qry', filename);
            alert('The converted query has been added as the current query. Move can now be executed.');
        };
    });
});

function find_to_move(list_of_dicts){
    let move_qry = [];
    if ('StudyInstanceUID' in list_of_dicts[0]['query_response']['data'][0] || 'SeriesInstanceUID' in list_of_dicts[0]['query_response']['data'][0]){
        $.each(list_of_dicts, function (key, val) {
            $.each(val['query_response']['data'], function (i, v) {
                if ('StudyInstanceUID' in v) {
                    move_qry.push({'StudyInstanceUID': v['StudyInstanceUID']})
                } else {
                    move_qry.push({'SeriesInstanceUID': v['SeriesInstanceUID']})
                }
            })

        })

    } else {
        alert('autocoversion utility not successful');
    }
    return move_qry;
}

function set_store_status(data, target){
    let store_status_msg = '';
    if (data) {
        store_status_msg = 'stop'
    } else {
        store_status_msg = 'start'
    }
    $(target).text(store_status_msg);
}

function make_config_table(data, reference, target) {
    let html_string = '<table>';
    $(reference).each(function(idx, val) {
        if ($(val).attr("for") in data) {
            let my_value = '(value not set)';
            if (data[$(val).attr("for")] != ''){
                my_value = data[$(val).attr("for")]
            }
            html_string += '<tr><td>' + my_value + ' </td></tr>';
        } else {
            html_string += '<tr><td> </td></tr>';
        }
    });
    html_string += '</table>';
    $(target).html(html_string);
}

function save_json(json_object, parents, filename) {

        let data = {
            "configuration": configuration,
            "json_data": json_object,
            "parents": parents,
            "filename": filename + '.json'
        };

        $.ajax({
            type: 'post',
            url: '/dicomconnect/_save_json',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function () {
                alert('Successfully saved as ' + filename + '.json')
            }
        });
}

function run_query(query_type){
    let query_results = [];
    let queries = query_file;
    let total_queries = queries.length;

    let query_types = ['find', 'move'];
    console.assert(query_types.includes(query_type), {query_type: query_type, error: 'non valid query type'});


    let i = 0;
    let start_time = $.now().toString();
    $("#" + query_type + "_progress").attr('max', total_queries);

    run_next_query();

    function run_next_query() {
        let query_response;
        if(!queries[i]) {
            return
        }
        let cqs = {
            'query_type': query_type,
            'current_query': i,
            'total_queries': total_queries,
            'start_time': start_time,
            'current_time': $.now(),
            'diff_to_last': 0,
            'filename': query_type + '_' + start_time
        };
        let query_to_send = {
            "query": [queries[i]],
            "configuration": configuration,
            "cqs": cqs
        };

        $.ajax({
            type: 'post',
            url: '/dicomconnect/_query',
            contentType: 'application/json',
            data: JSON.stringify(query_to_send),
            success: function (data) {
                query_response = data[0];
            }
        }).done(function () {
            query_results.push({
                "query_id": i,
                "query": queries[i],
                "query_response": query_response
            });
            $.each(query_response, function (key, val) {
                $.each(val, function (i, data_element) {
                    tabulate(data_element, "#" + query_type + "_" + key );
                });
            });
            i++;
            $("#" + query_type + "_progress").val(i)
            run_next_query();
        });
    };
    return query_results;
};

function tabulate(single_dict, output_location){
    if ($(output_location).has('table').length == 0) {
        let header_row = '';
        let first_row = '';
        $.each(single_dict, function (key, val) {
            header_row += '<th>'+ key +'</th>';
            first_row += '<td>'+ val +'</td>';
        });
        let html_string = '<table><thead><tr>' + header_row + '</tr></thead><tbody><tr>' + first_row + '</tr></tbody></table>';
        $(output_location).html(html_string)
    } else {
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
        $(output_location + " table tbody tr:last").after(html_string);

    }

}

function getFormData($form){
    var unindexed_array = $form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
    });

    return indexed_array;
}
