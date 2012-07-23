# Make Users
INSERT INTO users (user_name, access_level) VALUES ('jcollins', 32);
INSERT INTO users (user_name, access_level) VALUES ('sharrell', 128);
INSERT INTO users (user_name, access_level) VALUES ('shuey', 64);

# Make Groups
INSERT INTO groups (group_name) VALUES ('cs');
INSERT INTO groups (group_name) VALUES ('eas');
INSERT INTO groups (group_name) VALUES ('bio');

# Make User-Group Assignments
INSERT INTO user_group_assignments
    (user_group_assignments_group_name, user_group_assignments_user_name)
  VALUES ('cs', 'sharrell');
INSERT INTO user_group_assignments
    (user_group_assignments_group_name, user_group_assignments_user_name)
  VALUES ('cs', 'shuey');
INSERT INTO user_group_assignments
    (user_group_assignments_group_name, user_group_assignments_user_name)
  VALUES ('bio', 'shuey');

# Create Zones
INSERT INTO zones (zone_name) VALUES ('cs.university.edu');
INSERT INTO zones (zone_name) VALUES ('bio.university.edu');
INSERT INTO zones (zone_name) VALUES ('eas.university.edu');

# Create Zone Origins
INSERT INTO zone_view_assignments 
    (zone_origin, zone_view_assignments_zone_type, zone_view_assignments_zone_name,
     zone_view_assignments_view_dependency, zone_options) 
    VALUES ('cs.university.edu.','master','cs.university.edu','any','(d.)');
INSERT INTO zone_view_assignments 
    (zone_origin, zone_view_assignments_zone_type, zone_view_assignments_zone_name, 
     zone_view_assignments_view_dependency, zone_options) 
    VALUES ('bio.university.edu.','master','bio.university.edu','any','(d.)');
INSERT INTO zone_view_assignments 
    (zone_origin, zone_view_assignments_zone_type, zone_view_assignments_zone_name,
     zone_view_assignments_view_dependency, zone_options) 
    VALUES ('eas.university.edu.','master','eas.university.edu','any','(d.)');

# Create Forward Zone Permissions
INSERT INTO forward_zone_permissions
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name,
     forward_zone_permissions_group_permission)
  VALUES ('cs', 'cs.university.edu', 'rw');
INSERT INTO forward_zone_permissions
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name,
     forward_zone_permissions_group_permission)
  VALUES ('cs', 'eas.university.edu', 'r');
INSERT INTO forward_zone_permissions
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name,
     forward_zone_permissions_group_permission)
  VALUES ('bio', 'bio.university.edu', 'rw');

# Create Reverse Range Permissions
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block,
     reverse_range_permissions_group_permission)
  VALUES ('cs', '192.168.0.0/24', 'rw');
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block,
     reverse_range_permissions_group_permission)
  VALUES ('bio', '192.168.0.0/24', 'r');
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block,
     reverse_range_permissions_group_permission) 
  VALUES ('bio', '192.168.1.0/24', 'rw');

# vi: set ai aw sw=2:
