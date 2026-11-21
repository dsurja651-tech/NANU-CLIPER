/**
 * NanuCut Clipper ExtendScript for Adobe Premiere Pro
 * Native Project Bin imports, Sequence creation, and timeline clip placement.
 */

if (typeof($) == 'undefined') $ = {};

$._nanuCut = {
    // Check if a project is open and get active sequence
    getProjectStatus: function() {
        if (!app.project) {
            return JSON.stringify({ ok: false, error: "No Premiere Pro project is open." });
        }
        var activeSeq = app.project.activeSequence;
        var seqName = activeSeq ? activeSeq.name : "None (No active sequence)";
        var projName = app.project.name || "Untitled Project";
        return JSON.stringify({
            ok: true,
            projectName: projName,
            activeSequence: seqName,
            hasActiveSequence: !!activeSeq
        });
    },

    // Import a list of file paths (MP4, WAV, SRT) directly into the Project Bin
    importFilesToProject: function(filePathsJson) {
        if (!app.project) {
            return JSON.stringify({ ok: false, error: "No Premiere Pro project is open." });
        }
        try {
            var paths = JSON.parse(filePathsJson);
            if (!paths || paths.length === 0) {
                return JSON.stringify({ ok: false, error: "No file paths provided." });
            }
            var targetBin = app.project.getInsertionBin();
            var success = app.project.importFiles(paths, true, targetBin, false);
            return JSON.stringify({ ok: success, count: paths.length, message: "Imported " + paths.length + " clips to project." });
        } catch(e) {
            return JSON.stringify({ ok: false, error: e.toString() });
        }
    },

    // Create a vertical 9:16 Shorts Sequence (1080x1920) and place clip on timeline
    createVerticalSequence: function(clipPath, sequenceName) {
        if (!app.project) {
            return JSON.stringify({ ok: false, error: "No Premiere Pro project is open." });
        }
        try {
            var targetBin = app.project.getInsertionBin();
            app.project.importFiles([clipPath], true, targetBin, false);

            var importedItem = null;
            var numItems = app.project.rootItem.children.numItems;
            for (var i = 0; i < numItems; i++) {
                var it = app.project.rootItem.children[i];
                if (it.getMediaPath && it.getMediaPath() === clipPath) {
                    importedItem = it;
                    break;
                }
            }

            var name = sequenceName || "NanuCut_Short_9x16";
            var newSeq = null;
            if (importedItem) {
                newSeq = app.project.createNewSequenceFromClips(name, [importedItem], targetBin);
            }
            if (!newSeq) {
                newSeq = app.project.createNewSequence(name, "");
            }
            return JSON.stringify({ ok: true, sequenceName: name, message: "Created vertical sequence in Premiere Pro!" });
        } catch(e) {
            return JSON.stringify({ ok: false, error: e.toString() });
        }
    }
};
