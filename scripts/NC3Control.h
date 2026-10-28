// Project-local melonDS frontend instrumentation, enabled only by NC3_CONTROL_PATH.
// Commands use existing UI-thread APIs; this does not patch the game ROM.
#include <QTimer>
#include <QFile>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

static void nc3StartControl(QObject* owner)
{
    const QString requestPath = qEnvironmentVariable("NC3_CONTROL_PATH");
    if (requestPath.isEmpty()) return;
    auto timer = new QTimer(owner);
    QObject::connect(timer, &QTimer::timeout, owner, [requestPath]() {
        QFile request(requestPath);
        if (!request.exists() || !request.open(QIODevice::ReadOnly)) return;
        auto doc = QJsonDocument::fromJson(request.readAll());
        request.close();
        request.remove();
        auto cmd = doc.object();
        QJsonObject reply{{"id", cmd["id"]}, {"ok", true}};
        QString op = cmd["op"].toString();
        int id = cmd["instance"].toInt(0);
        QString path = cmd["path"].toString();
        auto fail = [&](QString message) { reply["ok"] = false; reply["error"] = message; };
        if (op == "new") {
            int next = 0;
            while (next < kMaxEmuInstances && emuInstances[next]) ++next;
            if (next == kMaxEmuInstances) fail("No free instance");
            else {
                auto cfg = Config::GetLocalTable(next);
                cfg.SetBool("Gdb.Enabled", false);
                auto first = Config::GetLocalTable(0);
                for (int k = 0; k < 12; ++k) {
                    auto name = std::string("Keyboard.") + EmuInstance::buttonNames[k];
                    cfg.SetInt(name, first.GetInt(name));
                }
                reply["created"] = createEmuInstance();
                reply["instance"] = next;
            }
        } else if (id < 0 || id >= kMaxEmuInstances || !emuInstances[id]) {
            fail("No such emulator instance");
        } else {
            auto inst = emuInstances[id];
            auto thread = inst->getEmuThread();
            if (op == "status") {
                QJsonArray instances;
                for (int i = 0; i < kMaxEmuInstances; ++i) {
                    if (!emuInstances[i]) continue;
                    auto t = emuInstances[i]->getEmuThread();
                    instances.append(QJsonObject{{"instance", i},
                        {"running", t->emuIsRunning()}, {"active", t->emuIsActive()},
                        {"frames", double(t->nc3FrameCount.load())},
                        {"window", double(emuInstances[i]->getMainWindow()->winId())}});
                }
                reply["instances"] = instances;
            } else if (op == "boot") {
                QString error;
                if (!thread->bootROM(QStringList{path}, error)) fail(error);
            } else if (op == "pause") {
                thread->emuPause(false);
            } else if (op == "resume") {
                thread->emuUnpause(false);
            } else if (op == "step") {
                reply["target_frame"] = double(thread->nc3FrameCount.load() + 1);
                thread->emuFrameStep();
            } else if (op == "save") {
                if (!thread->saveState(path)) fail("saveState failed");
            } else if (op == "load") {
                if (!thread->loadState(path)) fail("loadState failed");
            } else if (op == "import-save") {
                if (!thread->importSavefile(path)) fail("importSavefile failed");
            } else if (op == "key-down" || op == "key-up") {
                QKeyEvent event(op == "key-down" ? QEvent::KeyPress : QEvent::KeyRelease,
                                cmd["key"].toInt(), Qt::NoModifier);
                QCoreApplication::sendEvent(inst->getMainWindow(), &event);
            } else if (op == "release-keys") {
                for (int i = 0; i < 12; ++i) {
                    int key = inst->getLocalConfig().GetInt(std::string("Keyboard.") + EmuInstance::buttonNames[i]);
                    QKeyEvent event(QEvent::KeyRelease, key, Qt::NoModifier);
                    QCoreApplication::sendEvent(inst->getMainWindow(), &event);
                }
            } else if (op == "touch") {
                int x = cmd["x"].toInt(), y = cmd["y"].toInt();
                if (x < 0 || x > 255 || y < 0 || y > 191) fail("Touch out of range");
                else inst->touchScreen(x, y);
            } else if (op == "release-touch") {
                inst->releaseScreen();
            } else if (op == "dump") {
                if (thread->emuIsRunning()) fail("Pause emulator before RAM dump");
                else if (!inst->getNDS()) fail("No DS running");
                else {
                    QSaveFile output(path);
                    if (!output.open(QIODevice::WriteOnly)) fail("Cannot open RAM output");
                    else {
                        output.write(reinterpret_cast<const char*>(inst->getNDS()->MainRAM), 0x400000);
                        if (!output.commit()) fail("RAM output commit failed");
                    }
                }
            } else fail("Unknown operation");
        }
        QSaveFile response(requestPath + ".result");
        if (response.open(QIODevice::WriteOnly)) {
            response.write(QJsonDocument(reply).toJson(QJsonDocument::Compact));
            response.commit();
        }
    });
    timer->start(20);
}
