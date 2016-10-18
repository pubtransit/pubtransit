var log = {

    debug: function () {
        this.emit(" DEBUG ", arguments);
    },

    info: function () {
        this.emit(" INFO  ", arguments);
    },

    warning: function() {
        this.emit("WARNING", arguments);
    },

    error: function() {
        this.emit(" ERROR ", arguments);
    },

    emit: function(level, args) {
        stringified = [];
        for(var i in args) {
            stringified.push(JSON.stringify(args[i]))
        }
        console.log(level + " | " + stringified.join(" "))
    }
};
