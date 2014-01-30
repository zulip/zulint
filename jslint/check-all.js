"use strict";

// Global variables, categorized by place of definition.
var globals =
    // Third-party libraries
      ' $ _ jQuery Spinner Handlebars XDate zxcvbn Intl mixpanel Notification'
    + ' LazyLoad Dropbox SockJS marked'

    // Node-based unit tests
    + ' module'

    // Cocoa<-> Javascript bridge
    + ' bridge'

    // index.html
    + ' page_params'

    // common.js
    + ' status_classes password_quality'

    // setup.js
    + ' csrf_token'

    // Modules, defined in their respective files.
    + ' compose compose_fade rows hotkeys narrow reload notifications_bar search subs'
    + ' composebox_typeahead server_events typeahead_helper notifications hashchange'
    + ' invite ui util activity timerender MessageList MessageListView blueslip unread stream_list'
    + ' message_edit tab_bar emoji popovers navigate people settings'
    + ' avatar feature_flags search_suggestion referral stream_color Dict'
    + ' Filter summary admin stream_data muting WinChan muting_ui Socket channel'

    // colorspace.js
    + ' colorspace'

    // tutorial.js
    + ' tutorial'

    // templates.js
    + ' templates'

    // alert_words.js
    + ' alert_words'

    // fenced_code.js
    + ' fenced_code'

    // echo.js
    + ' echo'

    // localstorage.js
    + ' localstorage'

    // zulip.js
    + ' all_msg_list home_msg_list narrowed_msg_list current_msg_list get_updates_params'
    + ' add_messages'
    + ' keep_pointer_in_view unread_messages_read_in_narrow'
    + ' respond_to_message recenter_view last_viewport_movement_direction'
    + ' scroll_to_selected get_private_message_recipient'
    + ' load_old_messages enable_unread_counts'
    + ' at_top_of_viewport at_bottom_of_viewport within_viewport'
    + ' process_visible_unread_messages mark_messages_as_read viewport '
    + ' load_more_messages reset_load_more_status have_scrolled_away_from_top'
    + ' maybe_scroll_to_selected recenter_pointer_on_display suppress_scroll_pointer_update'
    + ' mark_current_list_as_read message_range message_in_table process_loaded_for_unread'
    + ' mark_all_as_read message_unread process_read_messages unread_in_current_view'
    + ' fast_forward_pointer recent_subjects unread_subjects'
    + ' furthest_read server_furthest_read update_messages'
    + ' add_message_metadata'
    + ' mark_message_as_read batched_flag_updater'
    + ' send_summarize_in_home'
    + ' send_summarize_in_stream'
    + ' suppress_unread_counts'
    + ' msg_metadata_cache'
    + ' report_as_received'
    + ' insert_new_messages process_message_for_recent_subjects'
    ;


var options = {
    vars:     true,  // Allow multiple 'var' per function
    sloppy:   true,  // Don't require "use strict"
    white:    true,  // Lenient whitespace rules
    plusplus: true,  // Allow increment/decrement operators
    regexp:   true,  // Allow . and [^...] in regular expressions
    todo:     true,  // Allow "TODO" comments.
    newcap:   true,  // Don't assume that capitalized functions are
                     // constructors (and the converse)
    nomen:    true,  // Tolerate underscore at the beginning of a name
    stupid:   true   // Allow synchronous methods
};


// For each error.raw message, we can return 'true' to ignore
// the error.
var exceptions = {
    "Unexpected 'else' after 'return'." : function () {
        return true;
    },

    "Don't make functions within a loop." : function () {
        return true;
    },

    // We use typeof to test if a variable exists at all.
    "Unexpected 'typeof'. Use '===' to compare directly with {a}.": function (error) {
        return error.a === 'undefined';
    }
};


var fs     = require('fs');
var path   = require('path');
var JSLINT = require(path.join(__dirname, 'jslint')).JSLINT;

var cwd    = process.cwd();

var exit_code = 0;
var i;

// Drop 'node' and the script name from args.
for (i=0; i<2; i++) {
    process.argv.shift();
}

process.argv.forEach(function (filepath) {
    var contents = fs.readFileSync(filepath, 'utf8');
    var messages = [];

    // We mutate 'options' so be sure to clear everything.
    if (filepath.indexOf('static/js/') !== -1) {
        // Frontend browser code
        options.browser = true;
        options.node    = false;
        options.predef  = globals.split(/\s+/);
    } else {
        // Backend code for Node.js
        options.browser = false;
        options.node    = true;

        if (filepath.indexOf('zerver/tests/frontend/') !== -1) {
            // Include '$' and browser globals because we use them inside
            // casper.evaluate
            options.predef = ['casper', '$', 'document', 'window', 'set_global', 'add_dependencies'];
        } else {
            options.predef = [];
        }
    }

    if (!JSLINT(contents, options)) {
        JSLINT.errors.forEach(function (error) {
            if (error === null) {
                // JSLint stopping error
                messages.push('          (JSLint giving up)');
                return;
            }

            var exn = exceptions[error.raw];
            if (exn && exn(error)) {
                // Ignore this error.
                return;
            }

            // NB: this will break on a 10,000 line file
            var line = ('    ' + error.line).slice(-4);

            messages.push('    ' + line + '  ' + error.reason);
        });

        if (messages.length > 0) {
            exit_code = 1;

            console.log(path.relative(cwd, filepath));

            // Something very wacky happens if we do
            // .forEach(console.log) directly.
            messages.forEach(function (msg) {
                console.log(msg);
            });

            console.log('');
        }
    }
});

process.exit(exit_code);
