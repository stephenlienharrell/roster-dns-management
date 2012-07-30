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
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name)
  VALUES ('cs', 'cs.university.edu');
# Save inserted forward_zone_permissions identity for multiple permission inserts
SELECT forward_zone_permissions_id INTO @forward_zone_perm_id
FROM forward_zone_permissions WHERE forward_zone_permissions_group_name = 'cs'
AND forward_zone_permissions_zone_name = 'cs.university.edu';
PREPARE group_perms_stmt FROM "INSERT INTO group_forward_permissions
    (group_forward_permissions_forward_zone_permissions_id,
     group_forward_permissions_group_permission) VALUES
    (?, 'a'),(?, 'aaaa'),(?, 'cname'),(?, 'ns'),(?, 'soa')";
EXECUTE group_perms_stmt USING @forward_zone_perm_id, @forward_zone_perm_id,
    @forward_zone_perm_id, @forward_zone_perm_id, @forward_zone_perm_id;
DEALLOCATE PREPARE group_perms_stmt;
INSERT INTO forward_zone_permissions
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name)
  VALUES ('cs', 'eas.university.edu');
# Save inserted forward_zone_permissions identity for multiple permission inserts
SELECT forward_zone_permissions_id INTO @forward_zone_perm_id
FROM forward_zone_permissions WHERE forward_zone_permissions_group_name = 'cs'
AND forward_zone_permissions_zone_name = 'eas.university.edu';
PREPARE group_perms_stmt FROM "INSERT INTO group_forward_permissions
    (group_forward_permissions_forward_zone_permissions_id,
     group_forward_permissions_group_permission) VALUES
    (?, 'a'),(?, 'aaaa'),(?, 'cname')";
EXECUTE group_perms_stmt USING @forward_zone_perm_id, @forward_zone_perm_id,
    @forward_zone_perm_id;
DEALLOCATE PREPARE group_perms_stmt;
INSERT INTO forward_zone_permissions
    (forward_zone_permissions_group_name, forward_zone_permissions_zone_name)
  VALUES ('bio', 'bio.university.edu');
# Save inserted forward_zone_permissions identity for multiple permission inserts
SELECT forward_zone_permissions_id INTO @forward_zone_perm_id
FROM forward_zone_permissions WHERE forward_zone_permissions_group_name = 'bio'
AND forward_zone_permissions_zone_name = 'bio.university.edu';
PREPARE group_perms_stmt FROM "INSERT INTO group_forward_permissions
    (group_forward_permissions_forward_zone_permissions_id,
     group_forward_permissions_group_permission) VALUES
    (?, 'a'),(?, 'aaaa')";
EXECUTE group_perms_stmt USING @forward_zone_perm_id, @forward_zone_perm_id;
DEALLOCATE PREPARE group_perms_stmt;
# Create Reverse Range Permissions
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block)
  VALUES ('cs', '192.168.0.0/24');
# Save inserted reverse_range_permissions identity for multiple perm inserts
SELECT reverse_range_permissions_id INTO @reverse_range_perm_id
FROM reverse_range_permissions WHERE reverse_range_permissions_group_name = 'cs'
AND reverse_range_permissions_cidr_block = '192.168.0.0/24';
PREPARE group_perms_stmt FROM "INSERT INTO group_reverse_permissions
    (group_reverse_permissions_reverse_range_permissions_id,
     group_reverse_permissions_group_permission) VALUES
    (?, 'cname'),(?, 'ns'),(?, 'ptr'),(?, 'soa')";
EXECUTE group_perms_stmt USING @reverse_range_perm_id, @reverse_range_perm_id,
    @reverse_range_perm_id, @reverse_range_perm_id;
DEALLOCATE PREPARE group_perms_stmt;
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block)
  VALUES ('bio', '192.168.0.0/24');
# Save inserted reverse_range_permissions identity for multiple perm inserts
SELECT reverse_range_permissions_id INTO @reverse_range_perm_id
FROM reverse_range_permissions WHERE
reverse_range_permissions_group_name = 'bio' AND
reverse_range_permissions_cidr_block = '192.168.0.0/24';
PREPARE group_perms_stmt FROM "INSERT INTO group_reverse_permissions
    (group_reverse_permissions_reverse_range_permissions_id,
     group_reverse_permissions_group_permission) VALUES
    (?, 'cname'),(?, 'ptr')";
EXECUTE group_perms_stmt USING @reverse_range_perm_id, @reverse_range_perm_id;
DEALLOCATE PREPARE group_perms_stmt;
INSERT INTO reverse_range_permissions
    (reverse_range_permissions_group_name, reverse_range_permissions_cidr_block)
  VALUES ('bio', '192.168.1.0/24');
# Save inserted reverse_range_permissions identity for multiple perm inserts
SELECT reverse_range_permissions_id INTO @reverse_range_perm_id
FROM reverse_range_permissions WHERE
reverse_range_permissions_group_name = 'bio' AND
reverse_range_permissions_cidr_block = '192.168.1.0/24';
PREPARE group_perms_stmt FROM "INSERT INTO group_reverse_permissions
    (group_reverse_permissions_reverse_range_permissions_id,
     group_reverse_permissions_group_permission) VALUES
    (?, 'ptr')";
EXECUTE group_perms_stmt USING @reverse_range_perm_id;
DEALLOCATE PREPARE group_perms_stmt;

# vi: set ai aw sw=2:
