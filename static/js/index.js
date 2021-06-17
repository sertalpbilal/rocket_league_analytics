
var app = new Vue({
    el: '#app',
    data: {},
    computed: {},
    methods: {}
})


async function fetch_file_list() {
    console.log("xxx")
}

$(document).ready(() => {
    Promise.all([
        fetch_file_list()
        ]).then(() => {
            console.log('ready')
        })
})
