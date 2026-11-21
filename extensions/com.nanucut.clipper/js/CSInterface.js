/**
 * CSInterface 11.0 / Premiere Pro Integration Wrapper for NanuCut Clipper
 */

(function () {
    'use strict';

    function CSInterface() {}

    CSInterface.prototype.isPremierePro = function () {
        return typeof window.__adobe_cep__ !== "undefined";
    };

    CSInterface.prototype.evalScript = function (script, callback) {
        if (typeof window.__adobe_cep__ !== "undefined") {
            window.__adobe_cep__.evalScript(script, callback);
        } else {
            console.log("[Mock CEP] evalScript:", script);
            if (script.indexOf("getProjectStatus") !== -1) {
                if (callback) callback(JSON.stringify({
                    ok: true,
                    projectName: "Sample_Shorts_Project.prproj",
                    activeSequence: "Main_Timeline_Sequence",
                    hasActiveSequence: true
                }));
            } else if (script.indexOf("importFilesToProject") !== -1) {
                if (callback) callback(JSON.stringify({ ok: true, count: 1, message: "Imported clips to project bin." }));
            } else {
                if (callback) callback(JSON.stringify({ ok: true }));
            }
        }
    };

    CSInterface.prototype.getSystemPath = function (pathType) {
        if (typeof window.__adobe_cep__ !== "undefined") {
            return window.__adobe_cep__.getSystemPath(pathType);
        }
        return "C:/Users/panda/AppData/Roaming/Adobe/CEP/extensions/com.nanucut.clipper";
    };

    CSInterface.prototype.closeExtension = function () {
        if (typeof window.__adobe_cep__ !== "undefined") {
            window.__adobe_cep__.closeExtension();
        }
    };

    window.CSInterface = CSInterface;
})();
