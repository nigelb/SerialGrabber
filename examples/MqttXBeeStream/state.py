from fysom import Fysom

name="name"
src="src"
dst="dst"


ph_events = [
    {name:"maintenance_request", src:"live", dst: "maintenance_mode_request"},
    {name:"maintenance_response", src:"maintenance_mode_request", dst: "maintenance_mode"},

    {name:"calibrate_request", src:"maintenance_mode", dst: "calibrate_request"},
    {name:"calibrate_response", src:"calibrate_request", dst: "calibrate"},

    {name:"calibrate_ph_request", src: "calibrate", dst:"calibrate_ph_request"},
    {name:"calibrate_ph_response", src: "calibrate_ph_request", dst:"calibrate_ph"},

    {name:"calibrate_ph_3point_request", src: "calibrate_ph", dst:"calibrate_ph_3point_request"},
    {name:"calibrate_ph_3point_response", src: "calibrate_ph_3point_request", dst:"calibrate_ph_3point"},

    {name:"calibrate_ph_2point_request", src: "calibrate_ph", dst:"calibrate_ph_2point_request"},
    {name:"calibrate_ph_2point_response", src: "calibrate_ph_2point_request", dst:"calibrate_ph_2point"},

    {name:"calibrate_ph_1point_request", src: "calibrate_ph", dst:"calibrate_ph_1point_request"},
    {name:"calibrate_ph_1point_response", src: "calibrate_ph_1point_request", dst:"calibrate_ph_1point"},


    {name: "calibrate_ph_phase_1_start_request", src: ["calibrate_ph_1point", "calibrate_ph_2point", "calibrate_ph_3point"], dst:"calibrate_ph_phase_1_request"},
    {name: "calibrate_ph_phase_1_response", src:"calibrate_ph_phase_1_request", dst:"calibrate_ph_phase_1"},

    {name: "calibrate_ph_phase_1_data_response", src:"calibrate_ph_phase_1", dst:"calibrate_ph_phase_1"},


    {name: "calibrate_ph_phase_1_accept_request", src: "calibrate_ph_phase_1", dst:"calibrate_ph_phase_1_accept_request"},
    {name: "calibrate_ph_phase_1_accept_response", src: "calibrate_ph_phase_1_accept_request", dst: ["calibrate_ph_1point_complete", "calibrate_ph_2point_phase_1_complete", "calibrate_ph_3point_phase_1_complete"]},


    {name: "calibrate_ph_1point_complete_response", src: "calibrate_ph_1point_complete", dst: "calibrate"},


    {name: "calibrate_ph_phase_2_start_request", src: ["calibrate_ph_2point_phase_1_complete", "calibrate_ph_3point_phase_1_complete"], dst:"calibrate_ph_phase_2_request"},
    {name: "calibrate_ph_phase_2_response", src:"calibrate_ph_phase_2_request", dst:"calibrate_ph_phase_2"},

    {name: "calibrate_ph_phase_2_data_response", src:"calibrate_ph_phase_2", dst:"calibrate_ph_phase_2"},

    {name: "calibrate_ph_phase_2_accept_request", src: "calibrate_ph_phase_2", dst:"calibrate_ph_phase_2_accept_request"},
    {name: "calibrate_ph_phase_2_accept_response", src: "calibrate_ph_phase_2_accept_request", dst: ["calibrate_ph_2point_complete", "calibrate_ph_3point_phase_2_complete"]},

    {name: "calibrate_ph_2point_complete_response", src: "calibrate_ph_2point_complete", dst: "calibrate"},


    {name: "calibrate_ph_phase_3_start_request", src: ["calibrate_ph_3point_phase_2_complete"], dst:"calibrate_ph_phase_3_request"},
    {name: "calibrate_ph_phase_3_response", src:"calibrate_ph_phase_3_request", dst:"calibrate_ph_phase_3"},

    {name: "calibrate_ph_phase_3_data_response", src:"calibrate_ph_phase_3", dst:"calibrate_ph_phase_3"},

    {name: "calibrate_ph_phase_3_accept_request", src: "calibrate_ph_phase_3", dst:"calibrate_ph_phase_3_accept_request"},
    {name: "calibrate_ph_phase_3_accept_response", src: "calibrate_ph_phase_3_accept_request", dst: ["calibrate_ph_3point_complete"]},

    {name: "calibrate_ph_3point_complete_response", src: "calibrate_ph_3point_complete", dst: "calibrate"},
]

do_events=[

]

ec_events=[

]

fsm = Fysom({
    "initial": "live",
    "events": ph_events
})

if __name__ == "__main__":
    import pydot

    map={
        "calibrate_ph_phase_1_start_request":"calibrate_ph_phase_1_start_request(MID, 7.0)",
        "calibrate_ph_phase_2_start_request":"calibrate_ph_phase_2_start_request(LOW_OR_HIGH, FLUID_VALUE)",
        "calibrate_ph_phase_3_start_request":"calibrate_ph_phase_3_start_request(LOW_OR_HIGH, FLUID_VALUE)",

    }

    graph = pydot.Dot(graph_type='digraph')
    def lookup(i):
        if i in map: return map[i]
        return i


    for i in fsm._map:
        el = fsm._map[i]
        for fm in el:
            to = el[fm]
            print fm, to
            if type(to) == list:
                for tt in to:
                    graph.add_edge(pydot.Edge(fm, tt, label=lookup(i)))
            else:
                graph.add_edge(pydot.Edge(fm, to, label=lookup(i)))

    graph.write_png('calibrate_ph.png')