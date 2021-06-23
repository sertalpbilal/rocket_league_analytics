
var app = new Vue({
    el: '#app',
    data: {
        games: [],
        colors: ['#DE8892', 'white', '#9FDC7C'],
        thresholds: [0, 0.5, 1]
    },
    computed: {
        sorted_games() {
            let game_copy = _.cloneDeep(this.games)
            let col_func = d3.scaleLinear().domain(this.thresholds).range(this.colors)
            let outcome_colors = {
                'L': "rgba(222, 136, 146, 1)",
                'L*': "rgba(222, 136, 146, 0.5)",
                'W*': "rgba(159, 220, 124, 0.5)",
                'W': "rgba(159, 220, 124, 1)"
            }
            game_copy.forEach((g) => {
                g['win_color'] = col_func(g['P(Win)'] / 100)
                g['outcome_color'] = outcome_colors[g['Outcome']]
            })
            return game_copy.sort((a,b) => parseInt(b['StartTime']) - parseInt(a['StartTime']))
        }
    },
    methods: {
        init_table() {
            $("#game_list").DataTable().destroy();
            this.$nextTick(() => {
                $("#game_list").DataTable({
                    "order": [[ 2, 'desc' ]],
                    "lengthChange": true,
                    "pageLength": 10,
                    "searching": true,
                    "info": true,
                    "paging": true,
                    "columnDefs": [{
                        "targets": [0],
                        "orderable": false
                        }],
                    "fixedHeader": true,
                    "scrollX": true
                });
            })
        },
        send_game_page(e) {
            let tm = e.currentTarget.dataset.href
            window.location = tm
        }
    }
})

async function fetch_file_list() {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "GET",
            url: `data/tables/scorelines.tsv`,
            dataType: "text",
            async: true,
            success: function(data) {
                tablevals = data.split('\n').map(i => i.split('\t').map(j => j.trim()));
                keys = tablevals[0];
                values = tablevals.slice(1);
                let el_data = values.map(i => _.zipObject(keys, i));
                app.games = el_data;
                app.$nextTick(() => {
                    app.init_table()
                })
            },
            error: function(xhr, status, error) {
                console.log(error);
                console.error(xhr, status, error);
                reject("No data");
            }
        });
    });
}

$(document).ready(() => {
    Promise.all([
        fetch_file_list()
        ]).then(() => {
            console.log('ready')
        })
})
