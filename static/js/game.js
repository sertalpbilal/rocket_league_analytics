
var app = new Vue({
    el: '#app',
    data: {
        game_id: "",
        shots: [],
        xg_out: [],
        colors: ['#DE8892', 'white', '#9FDC7C'],
        thresholds: [0, 0.5, 1]
    },
    computed: {
        shots_combined() {
            if (_.isEmpty(this.shots) || _.isEmpty(this.xg_out)) { return [] }
            let color_func = d3.scaleLinear().domain(this.thresholds).range(this.colors)
            let shots = _.cloneDeep(this.shots)
            let xg_out = _.cloneDeep(this.xg_out)
            shots.forEach((e, i) => {
                e['team_name'] = e['is_orange'] == 1 ? "Orange" : "Blue"
                e['team_color'] = e['is_orange'] == 1 ? "orange" : "blue"
                e['xg_info'] = xg_out[i]
                let game_xg = xg_out[i]['xg']
                e['xg_color'] = color_func(game_xg)
                e['goal_color'] = color_func((e['goal'] == 'True') + 0)
            })
            return shots
        }
    },
    methods: {
        init_shot_table() {
            $("#shot_list").DataTable().destroy();
            this.$nextTick(() => {
                $("#shot_list").DataTable({
                    "order": [[ 2, 'asc' ]],
                    "lengthChange": false,
                    "searching": true,
                    "info": false,
                    "paging": false,
                    "columnDefs": [{
                        "targets": [3],
                        "orderable": false
                        }],
                    "fixedHeader": true,
                    "scrollX": true
                });
            })
        }
    }
})

async function fetch_local_file(file) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "GET",
            url: file,
            dataType: "text",
            async: true,
            success: function(data) {
                resolve(data)
            },
            error: function(xhr, status, error) {
                console.log(error);
                console.error(xhr, status, error);
                reject("No data");
            }
        });
    });
}

async function fetch_game_shots() {
    return fetch_local_file('data/shots/' + app.game_id + '.csv').then((data) => {
        tablevals = data.split('\n').map(i => i.split(','));
        keys = tablevals[0];
        values = tablevals.slice(1).filter(i => i[0]);
        let zip_data = values.map(i => _.zipObject(keys, i));
        app.shots = zip_data
    })
}

async function fetch_game_xg() {
    return fetch_local_file('data/xg_out/' + app.game_id + '.csv').then((data) => {
        tablevals = data.split('\n').map(i => i.split(','));
        keys = tablevals[0];
        values = tablevals.slice(1).filter(i => i[0]);
        let zip_data = values.map(i => _.zipObject(keys, i));
        app.xg_out = zip_data
    })
}

$(document).ready(() => {

    var queryDict = {}
    location.search.substr(1).split("&").forEach((item) => {
        queryDict[item.split("=")[0]] = item.split("=")[1]
    })
    console.log(queryDict)
    app.game_id = queryDict['id']

    Promise.all([
            fetch_game_shots(),
            fetch_game_xg()
        ]).then(() => {
            console.log('ready')
            app.init_shot_table()
        })
})
