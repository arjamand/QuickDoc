#include <pybind11/embed.h>
#include <iostream>
#include <string>

using namespace std;
namespace py = pybind11;

void transcribeContinuousWithFilter() {
    try {
        py::scoped_interpreter guard{}; // Initialize Python interpreter
        auto whisper_with_filter = py::module::import("whisper-asr-v5"); // Import modified Python script

        // Call the transcribe_continuous_with_filter function
        whisper_with_filter.attr("__name__")();
    } catch (const py::error_already_set& e) {
        cerr << "Python Error: " << e.what() << endl;
    }
}

int main() {
    cout << "Continuous Real-Time ASR with Noise Filtering" << endl;
    transcribeContinuousWithFilter();
    return 0;
}
