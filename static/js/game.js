
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
                e['xg'] = parseFloat(game_xg)
                e['xg_color'] = color_func(game_xg)
                e['goal_color'] = color_func((e['goal'] == 'True') + 0)
                if (! e['time']) {
                    e['time'] = "300"
                }
                e['time'] = parseInt(e['time'])
                e['sec'] = (parseInt(e['frame'])/27.5 - 3).toFixed(2)
                e['x_mult'] = e['is_orange'] == 1 ? -1 : 1
                e['y_mult'] = e['is_orange'] == 1 ? 1 : -1
                e['order'] = i
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
                        "targets": [4],
                        "orderable": false
                        }],
                    "fixedHeader": true,
                    "scrollX": true
                });
            })
        }
    }
})

function plot_pitch_shot() {

    const raw_width = 12080+20;
    const raw_height = 8240+20;

    // 5140 y max (in svg it is x)
    // 4100 x max (in svg it is y)

    const margin = { top: 10, right: 10, bottom: 10, left: 10 },
        width = raw_width - margin.left - margin.right,
        height = raw_height - margin.top - margin.bottom;

    const svg = d3.select("#pitch_with_shots")
        .append("svg")
        .attr("viewBox", `0 0  ${(width + margin.left + margin.right)} ${(height + margin.top + margin.bottom)}`)
        .attr("id", "fixture_plot")
        .attr('class', 'w-100')
        .append('g')
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    let data = app.shots_combined

    let pitch = (context) => {
        context.moveTo(6040, 0);
        context.lineTo(1900, 0);
        context.lineTo(900, 1000);
        context.lineTo(900, 3170);
        context.lineTo(0, 3170);
        context.lineTo(0, 5070);
        context.lineTo(900, 5070);
        context.lineTo(900, 7240);
        context.lineTo(1900, 8240);
        context.lineTo(6040, 8240);
        context.lineTo(6040, 0);

        context.lineTo(10180,0);
        context.lineTo(11180,1000)
        context.lineTo(11180,3170)
        context.lineTo(12080,3170)
        context.lineTo(12080,5070)
        context.lineTo(11180,5070)
        context.lineTo(11180,7240)
        context.lineTo(10180,8240)
        context.lineTo(6040,8240)

        return context;
    }

    // pitch
    svg.append("path")
        .style("stroke", "black")
        .style("stroke-width", 50)
        .style("fill", "#f3f9ff")
        .attr("d", pitch(d3.path()))


    // y-axis
    let min_y = -4120 //Math.min(...data.map(i => i.ball_pos_x))
    let max_y = 4120 //Math.max(...data.map(i => i.ball_pos_x))
    const y = d3.scaleLinear().domain([min_y, max_y]).range([0, height])
    svg.append('g')
        .attr("id", "y-axis-holder")
        .attr("class", "axis-holder")
        .call(
            d3.axisRight(y).tickValues([-3120, -950, 0, 950, 3120])
            .tickSize(width)
            .tickFormat("")
        );

    // x-axis
    let min_x = -6040 //Math.min(...data.map(i => i.ball_pos_y))
    let max_x = 6040 // Math.max(...data.map(i => i.ball_pos_y))
    const x = d3.scaleLinear().domain([min_x, max_x]).range([0, width])
    svg.append('g')
        .attr("id", "x-axis-holder")
        .attr("class", "axis-holder")
        .call(
            d3.axisBottom(x).tickValues([-6040, -5140, -4140, -2070, 0, 2070, 4140, 5140, 6040])
            .tickSize(height)
            .tickFormat("")
        );
    
    svg.selectAll(".axis-holder")
        // .attr("font-size", "140pt")
        .attr("color", "purple")
        .attr("stroke-width", 20)
        .attr("stroke-dasharray", "150,80")
        .attr("stroke-opacity", 0.04)

    function highlight_shot (event,d) {
        let target = d3.select(event.currentTarget)
        target.style("fill-opacity", 1)
        d3.selectAll(".xg-entry").filter(i => i !== d).style("display", "none")
        // add all members
        let ff = svg.append("g").attr("id","frozen_frame")

        // team_mate
        ff.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", d.is_orange == 1 ? "orange" : "blue")
        .attr("d", d3.symbol().size(xg_size(0.5)).type(d3.symbolSquare)())
        .attr("transform", `translate(${x(d.x_mult * d.team_mate_pos_y)},${y(d.y_mult * d.team_mate_pos_x)})`)
        .attr("fill-opacity", 0.5)
        .style("pointer-events", "none")
        // opp 1
        ff.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", d.is_orange == 1 ? "blue" : "orange")
        .attr("d", d3.symbol().size(xg_size(0.5)).type(d3.symbolSquare)())
        .attr("transform", `translate(${x(d.x_mult * d.opp_1_pos_y)},${y(d.y_mult * d.opp_1_pos_x)})`)
        .attr("fill-opacity", 0.5)
        .style("pointer-events", "none")
        // opp 2
        ff.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", d.is_orange == 1 ? "blue" : "orange")
        .attr("d", d3.symbol().size(xg_size(0.5)).type(d3.symbolSquare)())
        .attr("transform", `translate(${x(d.x_mult * d.opp_2_pos_y)},${y(d.y_mult * d.opp_2_pos_x)})`)
        .attr("fill-opacity", 0.5)
        .style("pointer-events", "none")
        // ball
        ff.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 3)
        .style("stroke-width", 20)
        .style("fill", "gray")
        .attr("d", d3.symbol().size(xg_size(0.4)).type(d3.symbolCircle)())
        .attr("transform", `translate(${x(d.x_mult * d.ball_pos_y)},${y(d.y_mult * d.ball_pos_x)})`)
        .attr("fill-opacity", 0.4)
        .style("pointer-events", "none")
        
        $("#shot-" + d.order).addClass("higlighted-row")

    }
    function undo_higlight(event,d) {
        let target = d3.select(event.currentTarget)
        target.style("fill-opacity", 0.5)
        d3.select("#frozen_frame").remove()
        d3.selectAll(".xg-entry").style("display", "inline")
        $("#shot-" + d.order).removeClass("higlighted-row")
    }

    let shots = svg.append('g')
        .attr("id", "shot_container")
        .selectAll()
        .data(data.filter(i => i.goal == "False"))
        .enter()

    let xg_0 = 10000
    let xg_1 = 150000
    let xg_size = (v) => {
        return v * (xg_1 - xg_0) + xg_0
    }

    shots.append("path")
        .attr("class", "shot-circles xg-entry")
        .attr("id", (d) => 'marker-' + d.order)
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", (d) => d.is_orange == 1 ? "orange" : "blue")
        .attr("d", (d) => d3.symbol().size(xg_size(d.xg)).type(d3.symbolCircle)())
        .attr("transform", (d) => `translate(${x(d.x_mult * d.shot_taker_pos_y)},${y(d.y_mult * d.shot_taker_pos_x)})`)
        .attr("fill-opacity", 0.5)
        .on("mouseover", highlight_shot)
        .on("mouseleave", undo_higlight)

    let goals = svg.append('g')
        .attr("id", "goal_container")
        .selectAll()
        .data(data.filter(i => i.goal == "True"))
        .enter()
    
    goals.append("path")
        .attr("class", "goal-stars xg-entry")
        .attr("id", (d) => 'marker-' + d.order)
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", (d) => d.is_orange == 1 ? "orange" : "blue")
        .attr("d", (d) => d3.symbol().size(xg_size(d.xg)).type(d3.symbolStar)())
        .attr("transform", (d) => `translate(${x(d.x_mult * d.shot_taker_pos_y)},${y(d.y_mult * d.shot_taker_pos_x)})`)
        .attr("fill-opacity", 0.5)
        .on("mouseover", highlight_shot)
        .on("mouseleave", undo_higlight)

}

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
        tablevals =$.csv.toArrays(data);
        keys = tablevals[0];
        values = tablevals.slice(1).filter(i => i[0]);
        let zip_data = values.map(i => _.zipObject(keys, i));
        app.shots = zip_data
    })
}

async function fetch_game_xg() {
    return fetch_local_file('data/xg_out/' + app.game_id + '.csv').then((data) => {
        tablevals = $.csv.toArrays(data);
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
            app.$nextTick(() => {
                app.init_shot_table()
                plot_pitch_shot()
            })
        })
})
