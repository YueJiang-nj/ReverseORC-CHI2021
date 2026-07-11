#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace reverse_orc {

constexpr double kEpsilon = 1e-8;

struct Size {
    double minimum;
    double preferred;
    double maximum;
};

struct Box {
    double left;
    double top;
    double width;
    double height;
};

struct Node {
    bool widget = false;
    std::string name;
    Size width{0, 0, 0};
    Size height{0, 0, 0};
    double weight = 1.0;
    std::string direction = "row";
    double gap = 0.0;
    bool fill = false;
    bool uniform = false;
    bool balanced = false;
    std::vector<std::unique_ptr<Node>> children;
};

struct Result {
    std::map<std::string, Box> boxes;
    double objective = 0.0;
    int levels_solved = 0;
    int local_solves = 0;
};

Size sum_size(const std::vector<Size>& sizes, double gaps) {
    Size result{gaps, gaps, gaps};
    for (const auto& size : sizes) {
        result.minimum += size.minimum;
        result.preferred += size.preferred;
        result.maximum += size.maximum;
    }
    return result;
}

Size max_size(const std::vector<Size>& sizes) {
    if (sizes.empty()) throw std::invalid_argument("cannot measure an empty size list");
    Size result = sizes.front();
    for (const auto& size : sizes) {
        result.minimum = std::max(result.minimum, size.minimum);
        result.preferred = std::max(result.preferred, size.preferred);
        result.maximum = std::max(result.maximum, size.maximum);
    }
    return result;
}

std::pair<Size, Size> intrinsic(const Node& node) {
    if (node.widget) return {node.width, node.height};
    std::vector<std::pair<Size, Size>> measured;
    measured.reserve(node.children.size());
    for (const auto& child : node.children) measured.push_back(intrinsic(*child));
    const double gaps = node.gap * static_cast<double>(node.children.size() - 1);
    std::vector<Size> widths, heights;
    for (const auto& item : measured) {
        widths.push_back(item.first);
        heights.push_back(item.second);
    }
    if (node.direction == "horizontal_flow") {
        const Size max_width = max_size(widths);
        const Size max_height = max_size(heights);
        const Size sum_width = sum_size(widths, gaps);
        const Size sum_height = sum_size(heights, gaps);
        return {{max_width.minimum, sum_width.preferred, sum_width.maximum},
                {max_height.minimum, max_height.preferred, sum_height.maximum}};
    }
    if (node.direction == "vertical_flow") {
        const Size max_width = max_size(widths);
        const Size max_height = max_size(heights);
        const Size sum_width = sum_size(widths, gaps);
        const Size sum_height = sum_size(heights, gaps);
        return {{max_width.minimum, max_width.preferred, sum_width.maximum},
                {max_height.minimum, sum_height.preferred, sum_height.maximum}};
    }
    if (node.direction == "row") return {sum_size(widths, gaps), max_size(heights)};
    return {max_size(widths), sum_size(heights, gaps)};
}

std::vector<double> allocate(const std::vector<Size>& sizes,
                             const std::vector<double>& weights,
                             double available, bool fill = true) {
    double minimum = 0.0, maximum = 0.0, preferred = 0.0;
    for (const auto& size : sizes) {
        minimum += size.minimum;
        maximum += size.maximum;
        preferred += size.preferred;
    }
    if (available + kEpsilon < minimum)
        throw std::invalid_argument("container is smaller than the children's minimum size");
    double target = fill ? std::min(available, maximum) : std::min(available, preferred);
    target = std::max(target, minimum);
    auto values = [&](double lambda) {
        std::vector<double> result;
        result.reserve(sizes.size());
        for (std::size_t i = 0; i < sizes.size(); ++i) {
            const double weight = std::max(weights[i], 1e-12);
            result.push_back(std::min(sizes[i].maximum,
                std::max(sizes[i].minimum, sizes[i].preferred + lambda / (2.0 * weight))));
        }
        return result;
    };
    auto total = [](const std::vector<double>& items) {
        return std::accumulate(items.begin(), items.end(), 0.0);
    };
    double lo = -1.0, hi = 1.0;
    while (total(values(lo)) > target) lo *= 2.0;
    while (total(values(hi)) < target) hi *= 2.0;
    for (int iteration = 0; iteration < 70; ++iteration) {
        const double mid = (lo + hi) / 2.0;
        if (total(values(mid)) < target) lo = mid;
        else hi = mid;
    }
    return values((lo + hi) / 2.0);
}

class Solver {
public:
    Result solve(const Node& root, double width, double height, double left, double top) {
        if (width < 0 || height < 0)
            throw std::invalid_argument("canvas dimensions cannot be negative");
        const auto measured = intrinsic(root);
        if (width < measured.first.minimum || height < measured.second.minimum)
            throw std::invalid_argument("canvas is smaller than the root's minimum intrinsic size");
        Result result;
        place(root, {left, top, width, height}, result, 0);
        return result;
    }

private:
    using Line = std::vector<const Node*>;

    std::vector<Line> flow_lines(const Node& group, double capacity, bool horizontal) {
        std::vector<Line> lines;
        Line current;
        double used_min = 0.0, used_pref = 0.0;
        for (const auto& owned_child : group.children) {
            const Node* child = owned_child.get();
            const auto measured = intrinsic(*child);
            const Size size = horizontal ? measured.first : measured.second;
            double extra = current.empty() ? 0.0 : group.gap;
            if (!current.empty() &&
                (used_pref + extra + size.preferred > capacity + kEpsilon ||
                 used_min + extra + size.minimum > capacity + kEpsilon)) {
                lines.push_back(current);
                current.clear();
                used_min = used_pref = extra = 0.0;
            }
            if (size.minimum > capacity + kEpsilon)
                throw std::invalid_argument("a flow child is wider/taller than its container");
            current.push_back(child);
            used_min += extra + size.minimum;
            used_pref += extra + size.preferred;
        }
        if (!current.empty()) lines.push_back(current);
        if (group.balanced && lines.size() > 1) {
            std::vector<Line> balanced;
            const std::size_t count = group.children.size();
            const std::size_t line_count = lines.size();
            const std::size_t base = count / line_count;
            const std::size_t extra = count % line_count;
            std::size_t start = 0;
            for (std::size_t index = 0; index < line_count; ++index) {
                const std::size_t length = base + (index < extra ? 1 : 0);
                Line line;
                for (std::size_t i = 0; i < length; ++i)
                    line.push_back(group.children[start + i].get());
                balanced.push_back(std::move(line));
                start += length;
            }
            return balanced;
        }
        return lines;
    }

    Size flow_cross_size(const Node& group, double capacity, bool horizontal) {
        const auto lines = flow_lines(group, capacity, horizontal);
        std::vector<Size> line_sizes;
        for (const auto& line : lines) {
            std::vector<Size> cross;
            for (const Node* child : line) {
                const auto measured = intrinsic(*child);
                cross.push_back(horizontal ? measured.second : measured.first);
            }
            line_sizes.push_back(max_size(cross));
        }
        return sum_size(line_sizes, group.gap * static_cast<double>(lines.size() - 1));
    }

    void place(const Node& node, const Box& box, Result& result, int depth) {
        if (result.boxes.count(node.name))
            throw std::invalid_argument("node names must be unique: " + node.name);
        result.boxes[node.name] = box;
        result.levels_solved = std::max(result.levels_solved, depth + 1);
        if (node.widget) {
            const double width_delta = box.width - node.width.preferred;
            const double height_delta = box.height - node.height.preferred;
            result.objective += node.weight *
                (width_delta * width_delta + height_delta * height_delta);
            return;
        }
        ++result.local_solves;
        if (node.direction == "row" || node.direction == "column")
            place_linear(node, box, result, depth);
        else
            place_flow(node, box, result, depth);
    }

    void place_linear(const Node& group, const Box& box, Result& result, int depth) {
        const bool horizontal = group.direction == "row";
        std::vector<std::pair<Size, Size>> measured;
        for (const auto& child : group.children) measured.push_back(intrinsic(*child));
        for (std::size_t index = 0; index < group.children.size(); ++index) {
            const Node& child = *group.children[index];
            if (child.widget) continue;
            if (!horizontal && child.direction == "horizontal_flow")
                measured[index].second = flow_cross_size(child, box.width, true);
            else if (horizontal && child.direction == "vertical_flow")
                measured[index].first = flow_cross_size(child, box.height, false);
        }
        std::vector<Size> sizes;
        std::vector<double> weights;
        for (std::size_t i = 0; i < group.children.size(); ++i) {
            sizes.push_back(horizontal ? measured[i].first : measured[i].second);
            weights.push_back(group.children[i]->weight);
        }
        const double extent = (horizontal ? box.width : box.height) -
            group.gap * static_cast<double>(sizes.size() - 1);
        const auto allocated = allocate(sizes, weights, extent);
        double cursor = horizontal ? box.left : box.top;
        for (std::size_t i = 0; i < group.children.size(); ++i) {
            Box child_box = horizontal
                ? Box{cursor, box.top, allocated[i], box.height}
                : Box{box.left, cursor, box.width, allocated[i]};
            place(*group.children[i], child_box, result, depth + 1);
            cursor += allocated[i] + group.gap;
        }
    }

    void place_flow(const Node& group, const Box& box, Result& result, int depth) {
        const bool horizontal = group.direction == "horizontal_flow";
        const double capacity = horizontal ? box.width : box.height;
        const auto lines = flow_lines(group, capacity, horizontal);
        std::vector<Size> line_cross_sizes;
        for (const auto& line : lines) {
            std::vector<Size> cross;
            for (const Node* child : line) {
                const auto measured = intrinsic(*child);
                cross.push_back(horizontal ? measured.second : measured.first);
            }
            line_cross_sizes.push_back(max_size(cross));
        }
        const double cross_capacity = (horizontal ? box.height : box.width) -
            group.gap * static_cast<double>(lines.size() - 1);
        std::vector<double> line_weights(lines.size(), 1.0);
        auto line_extents = allocate(line_cross_sizes, line_weights, cross_capacity);
        if (group.uniform) {
            const double common = *std::min_element(line_extents.begin(), line_extents.end());
            std::fill(line_extents.begin(), line_extents.end(), common);
        }
        double cross_cursor = horizontal ? box.top : box.left;
        double uniform_primary = 0.0;
        if (group.uniform) {
            std::size_t largest = 0;
            for (const auto& line : lines) largest = std::max(largest, line.size());
            uniform_primary = (capacity - group.gap * static_cast<double>(largest - 1)) /
                              static_cast<double>(largest);
        }
        for (std::size_t line_index = 0; line_index < lines.size(); ++line_index) {
            const auto& line = lines[line_index];
            std::vector<Size> primary_sizes;
            std::vector<double> weights;
            for (const Node* child : line) {
                const auto measured = intrinsic(*child);
                primary_sizes.push_back(horizontal ? measured.first : measured.second);
                weights.push_back(child->weight);
            }
            const double primary_capacity = capacity -
                group.gap * static_cast<double>(line.size() - 1);
            std::vector<double> lengths;
            if (!group.uniform) {
                lengths = allocate(primary_sizes, weights, primary_capacity, group.fill);
            } else {
                double lower = -std::numeric_limits<double>::infinity();
                double upper = std::numeric_limits<double>::infinity();
                for (const auto& size : primary_sizes) {
                    lower = std::max(lower, size.minimum);
                    upper = std::min(upper, size.maximum);
                }
                const double common = std::min(upper, std::max(lower, uniform_primary));
                lengths.assign(line.size(), common);
            }
            double cursor = horizontal ? box.left : box.top;
            for (std::size_t i = 0; i < line.size(); ++i) {
                const Box child_box = horizontal
                    ? Box{cursor, cross_cursor, lengths[i], line_extents[line_index]}
                    : Box{cross_cursor, cursor, line_extents[line_index], lengths[i]};
                place(*line[i], child_box, result, depth + 1);
                cursor += lengths[i] + group.gap;
            }
            cross_cursor += line_extents[line_index] + group.gap;
        }
    }
};

}  // namespace reverse_orc

namespace {

PyObject* required_item(PyObject* dictionary, const char* key) {
    PyObject* value = PyDict_GetItemString(dictionary, key);
    if (!value) throw std::invalid_argument(std::string("missing node field: ") + key);
    return value;
}

double number(PyObject* value, const char* field) {
    const double result = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        throw std::invalid_argument(std::string(field) + " must be numeric");
    }
    return result;
}

std::string text(PyObject* value, const char* field) {
    if (!PyUnicode_Check(value)) throw std::invalid_argument(std::string(field) + " must be a string");
    const char* result = PyUnicode_AsUTF8(value);
    if (!result) throw std::invalid_argument(std::string(field) + " is not valid UTF-8");
    return result;
}

reverse_orc::Size parse_size(PyObject* value, const char* field) {
    if (!PySequence_Check(value) || PySequence_Size(value) != 3)
        throw std::invalid_argument(std::string(field) + " must contain minimum, preferred, maximum");
    PyObject* first = PySequence_GetItem(value, 0);
    PyObject* second = PySequence_GetItem(value, 1);
    PyObject* third = PySequence_GetItem(value, 2);
    if (!first || !second || !third) {
        Py_XDECREF(first); Py_XDECREF(second); Py_XDECREF(third);
        throw std::invalid_argument(std::string("invalid ") + field);
    }
    reverse_orc::Size result{number(first, field), number(second, field), number(third, field)};
    Py_DECREF(first); Py_DECREF(second); Py_DECREF(third);
    if (!(0 <= result.minimum && result.minimum <= result.preferred &&
          result.preferred <= result.maximum))
        throw std::invalid_argument("sizes must satisfy 0 <= minimum <= preferred <= maximum");
    return result;
}

std::unique_ptr<reverse_orc::Node> parse_node(PyObject* value) {
    if (!PyDict_Check(value)) throw std::invalid_argument("node must be a dictionary");
    auto node = std::make_unique<reverse_orc::Node>();
    node->name = text(required_item(value, "name"), "name");
    const std::string kind = text(required_item(value, "kind"), "kind");
    node->weight = number(required_item(value, "weight"), "weight");
    if (kind == "widget") {
        node->widget = true;
        node->width = parse_size(required_item(value, "width"), "width");
        node->height = parse_size(required_item(value, "height"), "height");
        return node;
    }
    if (kind != "group") throw std::invalid_argument("kind must be widget or group");
    node->direction = text(required_item(value, "direction"), "direction");
    if (node->direction != "row" && node->direction != "column" &&
        node->direction != "horizontal_flow" && node->direction != "vertical_flow")
        throw std::invalid_argument("invalid group direction");
    node->gap = number(required_item(value, "gap"), "gap");
    if (node->gap < 0) throw std::invalid_argument("gap cannot be negative");
    node->fill = PyObject_IsTrue(required_item(value, "fill"));
    node->uniform = PyObject_IsTrue(required_item(value, "uniform"));
    node->balanced = PyObject_IsTrue(required_item(value, "balanced"));
    PyObject* children = required_item(value, "children");
    if (!PySequence_Check(children) || PySequence_Size(children) < 1)
        throw std::invalid_argument("a group must contain at least one child");
    const Py_ssize_t count = PySequence_Size(children);
    for (Py_ssize_t index = 0; index < count; ++index) {
        PyObject* child = PySequence_GetItem(children, index);
        if (!child) throw std::invalid_argument("invalid child node");
        node->children.push_back(parse_node(child));
        Py_DECREF(child);
    }
    return node;
}

PyObject* py_solve(PyObject*, PyObject* args, PyObject* kwargs) {
    PyObject* root_object = nullptr;
    double width, height, left = 0.0, top = 0.0;
    static const char* keywords[] = {"root", "width", "height", "left", "top", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "Odd|dd",
                                     const_cast<char**>(keywords),
                                     &root_object, &width, &height, &left, &top))
        return nullptr;
    try {
        auto root = parse_node(root_object);
        reverse_orc::Solver solver;
        const auto solve_started = std::chrono::steady_clock::now();
        const auto result = solver.solve(*root, width, height, left, top);
        const double solver_seconds =
            std::chrono::duration<double>(std::chrono::steady_clock::now() - solve_started).count();
        PyObject* boxes = PyDict_New();
        for (const auto& item : result.boxes) {
            const auto& box = item.second;
            PyObject* tuple = Py_BuildValue("(dddd)", box.left, box.top, box.width, box.height);
            PyDict_SetItemString(boxes, item.first.c_str(), tuple);
            Py_DECREF(tuple);
        }
        PyObject* output = Py_BuildValue("{s:N,s:d,s:i,s:i,s:d}",
            "boxes", boxes, "objective", result.objective,
            "levels_solved", result.levels_solved, "local_solves", result.local_solves,
            "solver_seconds", solver_seconds);
        return output;
    } catch (const std::exception& error) {
        PyErr_SetString(PyExc_ValueError, error.what());
        return nullptr;
    }
}

PyMethodDef methods[] = {
    {"solve", reinterpret_cast<PyCFunction>(py_solve), METH_VARARGS | METH_KEYWORDS,
     "Solve a serialized hierarchical layout in C++."},
    {nullptr, nullptr, 0, nullptr}
};

PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_reverse_orc_cpp",
    "Native C++ hierarchical ReverseORC solver.", -1, methods
};

}  // namespace

PyMODINIT_FUNC PyInit__reverse_orc_cpp() { return PyModule_Create(&module); }
