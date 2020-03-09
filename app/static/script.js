// Client-side variables

let query_results = {};

$(document).ready(function(){

    $('#config_form').on('submit',function (e) {
        $.ajax({
            type: 'post',
            url: '/dicomconnect/_configuration',
            data: $('#config_form').serialize(),
            success: function (data) {
                let reference = "#config_form label";
                let target = "#config_form_results_table";
                make_config_table(data, reference, target);
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
                $("#query_preview").empty();
                $.each(q, function (key, val) {
                    tabulate(val, "#query_preview");
                })
                query_results['query'] = q;
                console.log(memorySizeOf(q));
            }
        });
        e.preventDefault();
    });

    $('#echo_button').click(function (response) {
        $.get('/dicomconnect/_echo', function (response) {
            alert(response);
        });
    });

    $('#find_button').click(function () {
        $("#find_progress").val(0)
        query_results['find'] = run_query('find');
    });

    $('#find_download').on('click', function () {
        _save_json('find');
    })

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
        _save_json('move');
    })

    $('#store_button').on('click', function () {
        $.get('/dicomconnect/_store', function (data) {
            set_store_status(data['store_status'], '#store_button')
        });
    });

    $(".overview-item-header").click(function () {

        $symbol = $(".expand-symbol", this);

        $content = $(this).next();
        //open up the content needed - toggle the slide- if visible, slide up, if not slidedown.
        $content.slideToggle(500, function () {
            //execute this after slideToggle is done
            //change text of header based on visibility of content div
            $symbol.text(function () {
                //change text based on condition
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
            $.ajax({
                type: 'post',
                url: '/dicomconnect/_query',
                contentType: 'application/json',
                data: JSON.stringify(move_qry)
            });
            query_results['query'] = move_qry;
            console.log(memorySizeOf(move_qry));
        }
    })

});


function find_to_move(list_of_dicts){
    let move_qry = [];
    console.log(list_of_dicts[0]['query_response']['data']);
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


function _save_json(query_type) {
    if (!query_type in query_results) {
        alert('No results for query type: ' + query_type);
    } else {
        let filename = query_type + '_' + String($.now());
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
    }
}

function run_query(query_type){

    let query_types = ['find', 'move'];
    let query_results = [];
    console.assert(query_types.includes(query_type), {query_type: query_type, error: 'non valid query type'} )

    $.getJSON('/dicomconnect/_query', function (queries) {
        var query_length = queries.length;
        var i = 0;

        $("#" + query_type + "_progress").attr('max', query_length);
        run_next_query();

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

                $.each(query_response, function (key, val) {
                    $.each(val, function (i, data_element) {
                        tabulate(data_element, "#" + query_type + "_" + key );
                    });
                });

                i++;

                $("#" + query_type + "_progress").val(i)

                run_next_query();
            })
        }
    })
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
















function memorySizeOf(obj) {
    var bytes = 0;

    function sizeOf(obj) {
        if(obj !== null && obj !== undefined) {
            switch(typeof obj) {
            case 'number':
                bytes += 8;
                break;
            case 'string':
                bytes += obj.length * 2;
                break;
            case 'boolean':
                bytes += 4;
                break;
            case 'object':
                var objClass = Object.prototype.toString.call(obj).slice(8, -1);
                if(objClass === 'Object' || objClass === 'Array') {
                    for(var key in obj) {
                        if(!obj.hasOwnProperty(key)) continue;
                        sizeOf(obj[key]);
                    }
                } else bytes += obj.toString().length * 2;
                break;
            }
        }
        return bytes;
    };

    function formatByteSize(bytes) {
        if(bytes < 1024) return bytes + " bytes";
        else if(bytes < 1048576) return(bytes / 1024).toFixed(3) + " KiB";
        else if(bytes < 1073741824) return(bytes / 1048576).toFixed(3) + " MiB";
        else return(bytes / 1073741824).toFixed(3) + " GiB";
    };

    return formatByteSize(sizeOf(obj));
};