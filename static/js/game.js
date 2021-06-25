
Object.fromEntries = Object.fromEntries || function(arr) {
    return arr.reduce(function(acc, curr) {
        acc[curr[0]] = curr[1];
        return acc;
    }, {});
};

var app = new Vue({
    el: '#app',
    data: {
        game_id: "",
        shots: [],
        xg_out: [],
        colors: ['#DE8892', 'white', '#9FDC7C'],
        thresholds: [0, 0.5, 1],
        game_json: {},
        main_player: "enpitsu",
        game_list: [],
        display_tags: [
            "xGF", "xGC", "xGD", "HF", "HC", "HD", "P(Win)", "P(Result)", "P(Score)", "Luck %", "Outcome"
        ]
    },
    computed: {
        shots_combined() {
            if (_.isEmpty(this.shots) || _.isEmpty(this.xg_out) || _.isEmpty(this.game_json)) { return [] }
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
                e['visible'] = game_xg > 0.05 || e['shot'] == 'True' || e['goal'] == 'True'
                e['fill'] = e['visible'] ? 0.5 : 0.1
                e['frameNumber'] = parseFloat(e['frame'])
            })

            // TODO: move goals here!!
            // // find shots
            // let goals = _.cloneDeep(this.game_json.gameMetadata.goals)
            // let players = this.game_json.players
            // let pdict = Object.fromEntries(players.map(i => [i.id.id, {'name': i.name, 'isOrange': i.isOrange}]))
            // goals.forEach((g) => {
            //     let p = pdict[g.playerId.id]
            //     g['isOrange'] = p.isOrange
            //     g['name'] = p.name
            //     // find closest hit for each goal

            // })


            return shots
        },
        our_team() {
            if (_.isEmpty(this.game_json)) { return {} }
            let are_we_orange = this.game_json.players.find(i => i.name == app.main_player).isOrange
            return are_we_orange ? "orange" : "blue"
        },
        c_team_name() {
            let our_team = this.our_team
            return {
                'orange': our_team == "orange" ? "US" : "THEM",
                'blue':  our_team == "blue" ? "US" : "THEM"
            }
        },
        team_orange() {
            if (_.isEmpty(this.game_json)) { return undefined }
            return this.game_json.teams.findIndex(i => i.isOrange)
        },
        team_blue() {
            if (_.isEmpty(this.game_json)) { return undefined }
            return this.game_json.teams.findIndex(i => !i.isOrange)
        },
        step_function_data() {
            if (_.isEmpty(this.shots_combined)) { return {} }
            let hits = this.shots_combined
            let goals = _.cloneDeep(this.game_json.gameMetadata.goals)
            let players = this.game_json.players
            let pdict = Object.fromEntries(players.map(i => [i.id.id, {'name': i.name, 'isOrange': i.isOrange}]))
            goals.forEach((g) => {
                let p = pdict[g.playerId.id]
                g['isOrange'] = p.isOrange
                g['name'] = p.name
            })

            let get_hits = (v) => {
                let prev_time = 0;
                let prev_sum = 0;
                steps = []
                v.forEach((h) => {
                    steps.push({
                        'frame': parseInt(h.frame),
                        'past_time': prev_time,
                        'current_time': h.time,
                        'past_sum': prev_sum,
                        'current_sum': prev_sum + h.xg,
                        'value': h.xg,
                        'ref': h
                    })
                    prev_time = h.time
                    prev_sum = prev_sum + h.xg
                })
                steps.push({
                    'past_time': prev_time,
                    'current_time': this.game_json.gameMetadata.length,
                    'past_sum': prev_sum,
                    'current_sum': prev_sum,
                    'value': 0,
                    'ref': undefined
                })
                return steps
            }

            let blue_team_hits = hits.filter(i => i.is_orange=="0")
            let blue_steps = get_hits(blue_team_hits)

            let orange_team_hits = hits.filter(i => i.is_orange=="1")
            let orange_steps = get_hits(orange_team_hits)

            return {'hits': {'blue': blue_steps, 'orange': orange_steps}, goals}
        },
        navigation() {
            if (_.isEmpty(this.game_list)) return {}
            let games = this.game_list
            let this_index = games.findIndex(i => i['Replay ID'] == this.game_id)
            return {
                'prev': this_index < games.length-1 ? games[this_index+1] : undefined,
                'this_game': games[this_index],
                'next': this_index > 0 ? games[this_index-1] : undefined
            }
        }
    },
    methods: {
        init_shot_table() {
            $("#shot_list").DataTable().destroy();
            this.$nextTick(() => {
                let shot_list = $("#shot_list").DataTable({
                    "order": [[ 2, 'asc' ]],
                    "lengthChange": false,
                    "searching": true,
                    "info": false,
                    "paging": false,
                    "columnDefs": [{
                        "targets": [7],
                        "orderable": false
                        }],
                    "fixedHeader": true,
                    "scrollX": true
                });
            })

            

            // need to run
            // d3.select("#marker-7").dispatch("mouseover")
        },
        hover_row(e) {
            let tm = e.currentTarget.dataset.targetMarker
            d3.select("#"+tm).dispatch("mouseover")
        },
        leave_row(e) {
            let tm = e.currentTarget.dataset.targetMarker
            d3.select("#"+tm).dispatch("mouseleave")
        }
    }
})

function plot_pitch_shot() {

    const raw_width = 12080+20;
    const raw_height = 8240+20+580;

    // 5140 y max (in svg it is x)
    // 4100 x max (in svg it is y)

    const margin = { top: 10, right: 10, bottom: 10+580, left: 10 },
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

    let arrowPoints = [[0, 0], [0, 20], [20, 10]];

    svg.append('defs')
        .append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', [0, 0, 20, 20])
        .attr('refX', 10)
        .attr('refY', 10)
        .attr('markerWidth', 20)
        .attr('markerHeight', 20)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', d3.line()(arrowPoints))
        .attr('stroke', 'black');

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

    let blue_side = (context) => {
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
        return context;
    }

    let orange_side = (context) => {
        context.moveTo(6040, 0);
        context.lineTo(10180,0);
        context.lineTo(11180,1000)
        context.lineTo(11180,3170)
        context.lineTo(12080,3170)
        context.lineTo(12080,5070)
        context.lineTo(11180,5070)
        context.lineTo(11180,7240)
        context.lineTo(10180,8240)
        context.lineTo(6040,8240)
        context.lineTo(6040, 0);
        return context;
    }

    // // pitch
    // svg.append("path")
    //     .style("stroke", "black")
    //     .style("stroke-width", 50)
    //     .style("fill", "#f3f9ff")
    //     .attr("d", pitch(d3.path()))

    // pitch
    let blue_team = svg.append("g")
    blue_team.append("path")
        .style("stroke", "black")
        .style("stroke-width", 50)
        .style("stroke-opacity", 0.5)
        .style("fill", "#d0e0ff78")
        .attr("d", blue_side(d3.path()))
    let blue_mid = (6400+900)/2
    let team_y = 2000
    let score_y = 4120
    let xg_y = 6240
    let blue_xg = app.xg_out.filter(i => i.is_orange==0).map(i => parseFloat(i.xg)).reduce((a,b) => a+b,0).toFixed(2)
    blue_team.append("text")
        .attr("class", "bgtext")
        .text(app.c_team_name["blue"]) //.text("BLUE")
        .attr("y", team_y)
        .attr("x", blue_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "900pt")
    blue_team.append("text")
        .attr("class", "bgtext")
        .text(app.game_json.teams[app.team_blue].score)
        .attr("y", score_y)
        .attr("x", blue_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "2000pt")
    blue_team.append("text")
        .attr("class", "bgtext")
        .text(blue_xg)
        .attr("y", xg_y)
        .attr("x", blue_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "900pt")

    let orange_team = svg.append("g")
    orange_team.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 0.5)
        .style("stroke-width", 50)
        .style("fill", "#ffe0a780")
        .attr("d", orange_side(d3.path()))
    let orange_mid = (6400+11180)/2
    let orange_xg = app.xg_out.filter(i => i.is_orange==1).map(i => parseFloat(i.xg)).reduce((a,b) => a+b,0).toFixed(2)
    orange_team.append("text")
        .attr("class", "bgtext")
        .text(app.c_team_name["orange"]) //.text("ORANGE")
        .attr("y", team_y)
        .attr("x", orange_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "900pt")
    orange_team.append("text")
        .attr("class", "bgtext")
        .text(app.game_json.teams[app.team_orange].score)
        .attr("y", score_y)
        .attr("x", orange_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "2000pt")
    orange_team.append("text")
        .attr("class", "bgtext")
        .text(orange_xg)
        .attr("y", xg_y)
        .attr("x", orange_mid)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "lightgray")
        .style("font-size", "900pt")



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
        // ball velocity
        let ball_pos_now = [x(d.x_mult * d.ball_pos_y), y(d.y_mult * d.ball_pos_x)]
        let ball_pos_next = [x(d.x_mult * (parseFloat(d.ball_pos_y) + parseFloat(d.ball_vel_y)/25)), y(d.y_mult * (parseFloat(d.ball_pos_x) + parseFloat(d.ball_vel_x)/25))]
        ff
        .append('path')
        .attr('d', d3.line()([ball_pos_now, ball_pos_next]))
        .attr('stroke', 'black')
        .attr("stroke-width", 10)
        .attr('marker-end', 'url(#arrow)')
        .attr('fill', 'none');

        $("#shot-" + d.order).addClass("higlighted-row")

        step_function_callback.enter(d.time)

    }
    function undo_higlight(event,d) {
        let target = d3.select(event.currentTarget)
        target.style("fill-opacity", d.fill)
        d3.selectAll("#frozen_frame").remove()
        d3.selectAll(".xg-entry").style("display", "inline")
        $("#shot-" + d.order).removeClass("higlighted-row")
        step_function_callback.leave()
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
        .style("stroke-opacity", (d) => d.shot == 'True' ? 1 : 0.1)
        .style("stroke-width", 20)
        .style("fill", (d) => d.is_orange == 1 ? "orange" : "blue")
        .attr("d", (d) => d3.symbol().size(xg_size(d.xg)).type(d3.symbolCircle)())
        .attr("transform", (d) => `translate(${x(d.x_mult * d.shot_taker_pos_y)},${y(d.y_mult * d.shot_taker_pos_x)})`)
        .attr("fill-opacity", (d) => d.fill)
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
        .attr("fill-opacity", (d) => d.fill)
        .on("mouseover", highlight_shot)
        .on("mouseleave", undo_higlight)

    let legened = svg.append("g")
    legened.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", "black")
        .attr("d", d3.symbol().size(xg_size(0.5)).type(d3.symbolStar)())
        .attr("transform", `translate(${width/2+500},${height+350})`)
        .attr("fill-opacity", 0.5)
    legened.append("text")
        .text("Goal")
        .attr("y", height+380)
        .attr("x", width/2+1300)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "black")
        .style("font-size", "230pt")
    legened.append("path")
        .style("stroke", "black")
        .style("stroke-opacity", 1)
        .style("stroke-width", 20)
        .style("fill", "black")
        .attr("d", d3.symbol().size(xg_size(0.5)).type(d3.symbolCircle)())
        .attr("transform", `translate(${width/2-1500},${height+350})`)
        .attr("fill-opacity", 0.5)
    legened.append("text")
        .text("Shot")
        .attr("y", height+380)
        .attr("x", width/2-800)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "black")
        .style("font-size", "230pt")

}

let step_function_callback;

function plot_xg_timeline() {

    const raw_width = 500;
    const raw_height = 350;

    // 5140 y max (in svg it is x)
    // 4100 x max (in svg it is y)

    const margin = { top: 25, right: 25, bottom: 35, left: 40 },
        width = raw_width - margin.left - margin.right,
        height = raw_height - margin.top - margin.bottom;

    const svg = d3.select("#xG_timeline")
        .append("svg")
        .attr("viewBox", `0 0  ${(width + margin.left + margin.right)} ${(height + margin.top + margin.bottom)}`)
        .attr("id", "fixture_plot")
        .attr('class', 'w-100')
        .append('g')
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    let data = app.step_function_data

    // background

    // y-axis
    let min_y = 0
    let max_y = Math.max(...data.hits.blue.map(i => i.current_sum), ...data.hits.orange.map(i => i.current_sum)) + 0.5
    const y = d3.scaleLinear().domain([min_y, max_y]).range([height, 0])
    svg.append('g')
        .attr("id", "y-axis-holder")
        .attr("class", "axis-holder")
        .call(
            d3.axisLeft(y)
            .tickSize(width)
        )
        .attr("transform", "translate(" + width + ",0)")

    // x-axis
    let min_x = 0
    let max_x = app.game_json.gameMetadata.length
    const x = d3.scaleLinear().domain([min_x, max_x]).range([0, width])
    svg.append('g')
        .attr("id", "x-axis-holder")
        .attr("class", "axis-holder")
        .call(
            d3.axisBottom(x)
            .tickSize(height)
        )
        // .attr("transform", "translate(" + width + ",0)")
    

    // bg rect and hover function
    let bisect = d3.bisector(function(d) { return d.current_time; }).right
    step_function_callback = {
        'enter': (time) => {
            let xv = x(time)
            lg.attr("x1", xv)
            lg.attr("x2", xv)
            bcircle.attr("cx", xv)
            ocircle.attr("cx", xv)
            
            let idx = bisect(data.hits.blue, time)
            let yv = data.hits.blue[idx].past_sum
            bcircle.attr("cy", y(yv))
            blue_score.text(yv.toFixed(2))

            idx = bisect(data.hits.orange, time)
            yv = data.hits.orange[idx].past_sum
            ocircle.attr("cy", y(yv))
            orange_score.text(yv.toFixed(2))

            score.attr("x", xv)
            hover_g.attr('display', "block")
        },
        'leave': (e) => {
            lg.attr("x1", 0)
            lg.attr("x2", 0)
            hover_g.attr('display', "none")
        }
    }
    
    let hover_g = svg.append('g').attr('id', 'hover-g').attr("display", "none")
    let m_move = (event) => {
        let raw_x = d3.pointer(event)[0]
        let ctime = x.invert(raw_x)
        let left_most = bisect(data.hits.orange, ctime)
        step_function_callback.enter(ctime)
    }
    let m_leave = (e) => {
        step_function_callback.leave()
    }
    svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mousemove', m_move)
            .on('mouseleave', m_leave)
    let lg = hover_g.append("line")
        .attr("x1", 50)
        .attr("x2", 50)
        .attr("y1", y(max_y))
        .attr("y2", y(min_y))
        .attr("stroke", "red")
        .attr("stroke-width", 5)
        .attr("stroke-opacity", 0.2)
    let bcircle = hover_g.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", 6)
        .attr("fill", "blue")
        // .attr("stroke", "black")
        // .style("stroke-width", 2)
    let ocircle = hover_g.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", 6)
        .attr("fill", "orange")
        // .attr("stroke", "black")
        // .style("stroke-width", 2)
    let score = hover_g.append("text")
        .attr("class", "score-text")
        .text("")
        .attr("y", -4)
        .attr("x", width/2)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "bottom")
        .style("font-size", "8pt")
    let blue_score = score.append("tspan")
        .text("BLUE")
        .attr("fill", "blue")
    score.append("tspan")
        .text(" - ")
        .attr("fill", "black")
    let orange_score = score.append("tspan")
        .text("ORANGE")
        .attr("fill", "#ff6f00")

    svg.selectAll(".axis-holder .tick line")
        // .attr("font-size", "140pt")
        .attr("color", "purple")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,1")
        .attr("stroke-opacity", 0.2)

    svg.selectAll("#y-axis-holder .domain")
        .attr("color", "gray")
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 1)
        .attr("fill", '#e9f1e9')
    

    function draw_step(context, d) {
        context.moveTo(x(d.past_time), y(d.past_sum));
        context.lineTo(x(d.current_time), y(d.past_sum));
        context.lineTo(x(d.current_time), y(d.current_sum));
        return context;
    }

    let steps = svg.append('g')
        .attr('class', 'step-holder')

    var line = d3.line()
        .curve(d3.curveStepAfter)
        .x(function(d) { return x(d.current_time); })              
        .y(function(d) { return y(d.current_sum); });

    steps.append("path")
        .attr("d", line(data.hits.blue))
        .attr("stroke", "blue")
        .attr("fill", "none")
        .attr("stroke-width", 2)
        .style("pointer-events", "none");
    
    steps.append("path")
        .attr("d", line(data.hits.orange))
        .attr("stroke", "orange")
        .attr("fill", "none")
        .attr("stroke-width", 2)
        .style("pointer-events", "none");

    let goal_layer = svg.append('g')
        .attr("id", "goal-layer")
    let gbisect = d3.bisector((d) => d.frame).left
    let goal_hits = data.goals
    goal_hits.forEach((g) => {
        if (g.isOrange == 1) {
            let id = gbisect(data.hits.orange, g.frameNumber)
            g.ref = data.hits.orange[id-1]
        } else {
            let id = gbisect(data.hits.blue, g.frameNumber)
            g.ref = data.hits.blue[id-1]
        }
    })
    
    goal_layer.selectAll()
        .data(goal_hits.filter(i => i.ref))
        .enter()
        .append("circle")
        .attr("cx", (d) => x(d.ref.current_time))
        .attr("cy", (d) => y(d.ref.current_sum))
        .attr("r", 6)
        .attr("fill", "white")
        .attr("fill-opacity", 0.9)
        .attr("stroke", (d) => d.isOrange ? "orange" : "blue")
        .style("stroke-width", 2)
        .style("pointer-events", "none")
        

    svg.append("text")
        .text("xG Timeline")
        .attr("y", -15)
        .attr("x", width/2)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "bottom")
        .attr("fill", "black")
        .style("font-size", "10pt")

    svg.append("text")
        .text("Cumulative xG")
        // .attr("y", height/2)
        // .attr("x", 200)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "bottom")
        .attr("fill", "black")
        .style("font-size", "10pt")
        .attr("transform", `translate(-25, ${height/2}) rotate(-90)`)
    
    svg.append("text")
        .text("Time (secs)")
        // .attr("y", height/2)
        // .attr("x", 200)
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "hanging")
        .attr("fill", "black")
        .style("font-size", "10pt")
        .attr("transform", `translate(${width/2}, ${height+20})`)

    let legened = svg.append("g")
    legened.append("circle")
        .attr("cx", width/2+150)
        .attr("cy", height+25)
        .attr("r", 4)
        .attr("fill", "white")
        .attr("fill-opacity", 0.9)
        .attr("stroke", "gray")
        .style("stroke-width", 2)
        .style("pointer-events", "none")
    legened.append("text")
        .text("Goal")
        .attr("text-anchor", 'middle')
        .attr("alignment-baseline", "middle")
        .attr("fill", "gray")
        .style("font-size", "10pt")
        .attr("transform", `translate(${width/2+175}, ${height+26})`)

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

async function fetch_game_json() {
    return fetch_local_file('data/json/' + app.game_id + '.json').then((data) => {
        app.game_json = JSON.parse(data)
    })
}

async function fetch_file_list() {
    return fetch_local_file('data/tables/scorelines.tsv').then((data) => {
        tablevals = data.split('\n').map(i => i.split('\t').map(j => j.trim()));
        keys = tablevals[0];
        values = tablevals.slice(1);
        let el_data = values.map(i => _.zipObject(keys, i));
        app.game_list = el_data;
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
            fetch_game_xg(),
            fetch_game_json(),
            fetch_file_list()
        ]).then(() => {
            console.log('ready')
            app.$nextTick(() => {
                app.init_shot_table()
                plot_pitch_shot()
                plot_xg_timeline()
            })
        })
})
