#set collision_control Kp 0.05
set speed_control Kp 10
set speed_control Ki 0.01
#set speed_control Kd 0
#call collision_control set_heading 1.58
#call collision_control set_speed 2
set waypoint_control forward_speed 2
call waypoint_control clear_waypoints
call waypoint_control add_waypoint [20,0]
call waypoint_control add_waypoint [0, 10]
call waypoint_control add_waypoint [-10,0]
call waypoint_control add_waypoint [0,0]
set waypoint_control enabled true

