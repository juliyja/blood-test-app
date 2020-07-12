CKEDITOR.plugins.add('customDropdown',
    {
        requires: ['richcombo'], //, 'styles' ],
        init: function (editor) {
            config = editor.config;

            editor.ui.addRichCombo('my-combo', {
                label: 'Variables',
                title: 'Variables',
                toolbar: 'basicstyles,0',

                panel: {
                    css: [CKEDITOR.skin.getPath('editor')].concat(config.contentsCss),
                    multiSelect: false,
                    attributes: {'aria-label': 'Variables'}
                },

                init: function () {
                    this.startGroup('Variables');
                    this.add('$name', 'Name');
                    this.add('$surname', 'Surname');
                    this.add('$date', 'Test date');

                },

                onClick: function (value) {
                    editor.focus();
                    editor.fire('saveSnapshot');

                    editor.insertHtml(value);

                    editor.fire('saveSnapshot');
                }
            });
        }
    });