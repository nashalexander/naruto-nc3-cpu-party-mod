// Opt-in project-local capture shim for melonDS 0.9.5. ROM bytes are untouched.
#include <QTimer>
#include <QFile>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include "ARM.h"

static void nc3StartLegacyControl(QObject* owner)
{
    QString requestPath = qEnvironmentVariable("NC3_CONTROL_PATH");
    if (requestPath.isEmpty()) return;
    auto timer = new QTimer(owner);
    QObject::connect(timer, &QTimer::timeout, owner, [requestPath]() {
        QFile input(requestPath);
        if (!input.exists() || !input.open(QIODevice::ReadOnly)) return;
        auto cmd = QJsonDocument::fromJson(input.readAll()).object();
        input.close(); input.remove();
        QJsonObject reply{{"id", cmd["id"]}, {"ok", true}};
        auto fail = [&](QString error) { reply["ok"] = false; reply["error"] = error; };
        QString op = cmd["op"].toString(), path = cmd["path"].toString();
        if (op == "status") {
            reply["instances"] = QJsonArray{QJsonObject{{"instance", 0},
                {"active", emuThread->emuIsActive()}, {"running", emuThread->emuIsRunning()},
                {"paused", emuThread->nc3Paused()},
                {"frames", double(nc3LegacyFrames.load())}, {"window", double(mainWindow->winId())}}};
        } else if (op == "pause") emuThread->emuPause();
        else if (op == "resume") emuThread->emuUnpause();
        else if (op == "step") {
            if (!emuThread->nc3Paused()) fail("Pause before stepping");
            else {
                reply["target_frame"] = double(nc3LegacyFrames.load() + 1);
                emuThread->emuFrameStep();
            }
        } else if (op == "load" || op == "save") {
            bool running = emuThread->emuIsRunning();
            if (running) emuThread->emuPause();
            bool ok = op == "load" ? ROMManager::LoadState(path.toStdString())
                                     : ROMManager::SaveState(path.toStdString());
            if (!ok) fail("State operation failed");
            if (running) emuThread->emuUnpause();
        } else if (op == "key-down" || op == "key-up") {
            QKeyEvent key(op == "key-down" ? QEvent::KeyPress : QEvent::KeyRelease,
                          cmd["key"].toInt(), Qt::NoModifier);
            if (op == "key-down") Input::KeyPress(&key); else Input::KeyRelease(&key);
        } else if (op == "touch" || op == "release-touch") {
            if (emuThread->emuIsRunning()) fail("Pause before direct touch updates");
            else if (op == "touch") NDS::TouchScreen(cmd["x"].toInt(), cmd["y"].toInt());
            else NDS::ReleaseScreen();
        } else if (op == "shot") {
            if (!mainWindow->grab().save(path)) fail("Screenshot failed");
        } else if (op == "dump") {
            if (!emuThread->nc3Paused()) fail("Pause before memory capture");
            else {
                QSaveFile output(path);
                if (!output.open(QIODevice::WriteOnly)) fail("Cannot open dump");
                else {
                    output.write(reinterpret_cast<const char*>(NDS::MainRAM), 0x400000);
                    if (!output.commit()) fail("Dump commit failed");
                }
                QJsonArray regs;
                for (int i = 0; i < 16; ++i) regs.append(double(NDS::ARM9->R[i]));
                reply["registers_raw"] = regs;
                reply["cpsr"] = double(NDS::ARM9->CPSR);
            }
        } else if (op == "probe-write") {
            // Single-field visual validation only, with mandatory original bytes.
            auto original = QByteArray::fromHex(cmd["expected"].toString().toLatin1());
            auto replacement = QByteArray::fromHex(cmd["data"].toString().toLatin1());
            int offset = cmd["offset"].toInt(-1);
            if (!emuThread->nc3Paused()) fail("Pause before a field probe");
            else if (offset < 0 || original.isEmpty() || original.size() != replacement.size()
                     || original.size() > 16 || offset > 0x400000 - original.size()) fail("Invalid probe");
            else if (memcmp(NDS::MainRAM + offset, original.data(), original.size())) fail("Original-byte assertion failed");
            else memcpy(NDS::MainRAM + offset, replacement.data(), replacement.size());
        } else fail("Unknown operation");
        QSaveFile response(requestPath + ".result");
        if (response.open(QIODevice::WriteOnly)) {
            response.write(QJsonDocument(reply).toJson(QJsonDocument::Compact)); response.commit();
        }
    });
    timer->start(20);
}
