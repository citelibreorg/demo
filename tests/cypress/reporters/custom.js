'use strict';
require('node:http');
const Mocha = require('mocha');
const fs = require('node:fs');
const util = require('util');

const {
    EVENT_RUN_END,
    EVENT_TEST_FAIL,
    EVENT_TEST_PASS
} = Mocha.Runner.constants;

class MyReporter {
    constructor(runner) {

        const stats = runner.stats;
        let output = '';
        let testedApp = '';

        runner
            .on(EVENT_TEST_PASS, test => {
                testedApp = test.parent.title;
                const testName = test.title;
                const stepDuration = test.duration;

                const tags = 'testedApp="' + testedApp + '"' + ',testedScenario="' + testName + '"';


                output += '# TYPE caseDuration gauge\n' +
                    '# HELP caseDuration doc\n' +
                    'caseDuration{' + tags + '} ' + stepDuration + '\n' +
                    '# TYPE caseState gauge\n' +
                    '# HELP caseState doc\n' +
                    'caseState{' + tags + '} ' + 1 + '\n';


            })
            .on(EVENT_TEST_FAIL, (test, err) => {
                const codeFrame = err.codeFrame;
                if (codeFrame) {
                    console.log(`Test fail at line ${codeFrame.line} and col ${codeFrame.column}`);
                }

                testedApp = test.parent.title;
                const testName = test.title;

                const tags = 'testedApp="' + testedApp + '"' + ',testedScenario="' + testName + '"';


                output += '# TYPE caseDuration gauge\n' +
                    '# HELP caseDuration doc\n' +
                    'caseDuration{' + tags + '} ' + 0 + '\n' +
                    '# TYPE caseState gauge\n' +
                    '# HELP caseState doc\n' +
                    'caseState{' + tags + '} ' + 0 + '\n';

            })
            .once(EVENT_RUN_END, () => {

                const mainTags = 'testedApp="' + testedApp + '"';

                output += '# TYPE globalDuration gauge\n' +
                    '# HELP globalDuration doc\n' +
                    'globalDuration{' + mainTags + '} ' + stats.duration + '\n' +

                    '# TYPE globalFailures gauge\n' +
                    '# HELP globalFailures doc\n' +
                    'globalFailures{' + mainTags + '} ' + stats.failures + '\n' +

                    '# TYPE globalPasses gauge\n' +
                    '# HELP globalPasses doc\n' +
                    'globalPasses{' + mainTags + '} ' + stats.passes + '\n' +

                    '# TYPE globalTests gauge\n' +
                    '# HELP globalTests doc\n' +
                    'globalTests{' + mainTags + '} ' + stats.tests + '\n';

                console.log(`\n${output}`);

                if(!fs.existsSync('cypress/results')) {
                    fs.mkdirSync('cypress/results', {recursive: true});
                }

                fs.writeFile('cypress/results/metric.out', output, (ex) => {
                    if (ex) {
                        console.log(`metrics :: write :: error :: ${JSON.stringify(ex)}`);
                    } else {
                        console.log('metrics :: write :: ok');
                    }
                    console.log('metrics :: end');
                });
            });
    }
}

module.exports = MyReporter;
