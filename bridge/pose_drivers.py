import importlib

import numpy as np
from mathutils import Euler

import m_CONST
from _blender.utils import objects
from bridge import abs_assignment
from utils import m_V, log

importlib.reload(abs_assignment)
importlib.reload(m_CONST)


class BridgePose(abs_assignment.DataAssignment):
    def __init__(self):
        self.references = {
            # MEDIAPIPE DEFAULTS
            0: m_CONST.POSE.nose.value,
            1: m_CONST.POSE.left_eye_inner.value,
            2: m_CONST.POSE.left_eye.value,
            3: m_CONST.POSE.left_eye_outer.value,
            4: m_CONST.POSE.right_eye_inner.value,
            5: m_CONST.POSE.right_eye.value,
            6: m_CONST.POSE.right_eye_outer.value,
            7: m_CONST.POSE.left_ear.value,
            8: m_CONST.POSE.right_ear.value,
            9: m_CONST.POSE.mouth_left.value,
            10: m_CONST.POSE.mouth_right.value,
            11: m_CONST.POSE.left_shoulder.value,
            12: m_CONST.POSE.right_shoulder.value,
            13: m_CONST.POSE.left_elbow.value,
            14: m_CONST.POSE.right_elbow.value,
            15: m_CONST.POSE.left_wrist.value,
            16: m_CONST.POSE.right_wrist.value,
            17: m_CONST.POSE.left_pinky.value,
            18: m_CONST.POSE.right_pinky.value,
            19: m_CONST.POSE.left_index.value,
            20: m_CONST.POSE.right_index.value,
            21: m_CONST.POSE.left_thumb.value,
            22: m_CONST.POSE.right_thumb.value,
            23: m_CONST.POSE.left_hip.value,
            24: m_CONST.POSE.right_hip.value,
            25: m_CONST.POSE.left_knee.value,
            26: m_CONST.POSE.right_knee.value,
            27: m_CONST.POSE.left_ankle.value,
            28: m_CONST.POSE.right_ankle.value,
            29: m_CONST.POSE.left_heel.value,
            30: m_CONST.POSE.right_heel.value,
            31: m_CONST.POSE.left_foot_index.value,
            32: m_CONST.POSE.right_foot_index.value,

            # DRIVERS
            33: m_CONST.POSE.left_forearm_ik.value,
            34: m_CONST.POSE.right_forearm_ik.value,
            35: m_CONST.POSE.left_hand_ik.value,
            36: m_CONST.POSE.right_hand_ik.value,

            37: m_CONST.POSE.left_index_ik.value,
            38: m_CONST.POSE.right_index_ik.value,
            39: m_CONST.POSE.right_foot_ik.value,
            40: m_CONST.POSE.left_foot_ik.value,
            41: m_CONST.POSE.left_shin_ik.value,
            42: m_CONST.POSE.right_shin_ik.value,

            43: m_CONST.POSE.left_shoulder_ik.value,
            44: m_CONST.POSE.right_shoulder_ik.value,
        }

        self.arms = [
            [12, 17],  # right arm
            [11, 16]  # left arm_z
        ]

        self.legs = [
            [24, 29],  # right leg
            [23, 30]  # left leg
        ]

        self.shoulder_center = abs_assignment.CustomData()
        self.hip_center = abs_assignment.CustomData()

        self.pose = []
        self.col_name = m_CONST.COLLECTIONS.pose.value
        self.rotation_data = []
        self.scale_data = []

    def init_references(self):
        # default empties
        self.pose = objects.add_empties(self.references, 0.025)
        objects.add_list_to_collection(self.col_name, self.pose, self.driver_col)

        self.init_bpy_driver_obj(
            self.shoulder_center, self.pose, 0.01, m_CONST.POSE.shoulder_center.value, self.col_name, "SPHERE",
            [0, 0, 0])
        self.init_bpy_driver_obj(
            self.hip_center, self.pose, 0.01, m_CONST.POSE.hip_center.value, self.col_name, "SPHERE", [0, 0, 0])

    def init_data(self):
        self.rotation_data = []
        self.scale_data = []
        self.prepare_landmarks()
        self.average_rig_scale()
        self.shoulder_hip_location()
        self.shoulder_hip_rotation()

    def update(self):
        self.set_position()
        self.set_rotation()
        self.set_scale()

    def set_position(self):
        """Keyframe the position of input data."""
        try:
            self.translate(self.pose, self.data, self.frame)

        except IndexError:
            log.logger.error("VALUE ERROR WHILE ASSIGNING POSE POSITION")

    def set_rotation(self):
        self.euler_rotate(self.pose, self.rotation_data, self.frame)
        pass

    def set_scale(self):
        self.scale(self.pose, self.scale_data, self.frame)

    def average_rig_scale(self):
        self.arm_chain_lengths()
        self.leg_chain_lengths()

    def leg_chain_lengths(self):
        """ every segment changes length individually during the tracking process """
        # 23: left_hip, 25: left_knee, 29: left_heel, 27: left_ankle
        left_upper_leg_length = m_V.get_vector_distance(self.data[23][1], self.data[25][1])
        left_lower_leg_length = m_V.get_vector_distance(self.data[25][1], self.data[27][1])
        left_foot_length = m_V.get_vector_distance(self.data[27][1], self.data[29][1])

        # 24: right_hip, 26: right_knee, 28: right_ankle, 30: right_heel
        right_upper_leg_length = m_V.get_vector_distance(self.data[24][1], self.data[26][1])
        right_lower_leg_length = m_V.get_vector_distance(self.data[26][1], self.data[28][1])
        right_foot_length = m_V.get_vector_distance(self.data[28][1], self.data[30][1])

        data = [
            [23, [1, 1, left_upper_leg_length]],
            [24, [1, 1, right_upper_leg_length]],
            [25, [1, 1, left_lower_leg_length]],
            [26, [1, 1, right_lower_leg_length]],
            [27, [1, 1, left_foot_length]],
            [28, [1, 1, right_foot_length]]
        ]

        for d in data:
            self.scale_data.append(d)

    def arm_chain_lengths(self):
        """ every segment changes length individually during the tracking process """

        # 11: left_shoulder, 13: left_elbow, 15: left_wrist, 19: left_index
        right_upper_arm_length = m_V.get_vector_distance(self.data[12][1], self.data[14][1])
        right_forearm_length = m_V.get_vector_distance(self.data[14][1], self.data[16][1])
        right_wrist_length = m_V.get_vector_distance(self.data[16][1], self.data[20][1])

        # 12: right_shoulder, 14: right_elbow, 16: right_wrist, 20: right_index
        left_upper_arm_length = m_V.get_vector_distance(self.data[11][1], self.data[13][1])
        left_forearm_length = m_V.get_vector_distance(self.data[13][1], self.data[15][1])
        left_wrist_length = m_V.get_vector_distance(self.data[15][1], self.data[19][1])

        data = [
            [13, [1, 1, left_upper_arm_length]],
            [14, [1, 1, right_upper_arm_length]],
            [15, [1, 1, left_forearm_length]],
            [16, [1, 1, right_forearm_length]],
            [19, [1, 1, left_wrist_length]],
            [20, [1, 1, right_wrist_length]]
        ]

        for d in data:
            self.scale_data.append(d)

    def torso_rotation(self):
        # approximate perpendicular points to origin
        hip_center = m_V.center_point(np.array(self.data[23][1]), np.array(self.data[24][1]))
        right_hip = np.array(self.data[24][1])
        shoulder_center = m_V.center_point(np.array(self.data[11][1]), np.array(self.data[12][1]))

        # generate triangle
        vertices = np.array(
            [self.data[23][1],
             self.data[24][1],
             shoulder_center])
        connections = np.array([[0, 1, 2]])

        # get normal from triangle
        normal, norm = m_V.create_normal_array(vertices, connections)

        # direction vectors from imaginary origin
        tangent = m_V.normalize(m_V.to_vector(hip_center, right_hip))
        normal = m_V.normalize(normal[0])
        binormal = m_V.normalize(m_V.to_vector(hip_center, shoulder_center))

        # generate matrix to decompose it and access quaternion rotation
        matrix = m_V.generate_matrix(tangent, binormal, normal)
        loc, quart, scale = m_V.decompose_matrix(matrix)

        offset = [-.5, 0, 0]
        euler = self.try_get_euler(quart, offset, self.hip_center.idx)
        euler = self.offset_euler(euler, offset)

        return euler

    def shoulder_rotation(self):
        # rotation from shoulder center to shoulder.R
        shoulder_center = m_V.center_point(self.data[11][1], self.data[12][1])
        shoulder_rotation = m_V.rotate_towards(shoulder_center, self.data[12][1], 'Z')

        # rotation from hip center to hip.R
        hip_center = m_V.center_point(self.data[23][1], self.data[24][1])
        hip_rotation = m_V.rotate_towards(hip_center, self.data[24][1], 'Z')

        # chance to offset result / rotation may not be keyframed
        offset = [0, 0, 0]
        shoulder_euler = self.try_get_euler(shoulder_rotation, offset, 7)
        shoulder_rot = self.offset_euler(shoulder_euler, offset)

        hip_euler = self.try_get_euler(hip_rotation, offset, 8)
        hip_rot = self.offset_euler(hip_euler, offset)

        # offset between hip & shoulder rot = real shoulder rot
        euler = Euler((shoulder_rot[0] - hip_rot[0],
                       shoulder_rot[1] - hip_rot[1],
                       shoulder_rot[2] - hip_rot[2]))

        return euler

    def shoulder_hip_rotation(self):
        """ Creates custom rotation data for driving the rig. """
        self.shoulder_center.rot = self.shoulder_rotation()
        self.hip_center.rot = self.torso_rotation()

        # setup data format
        data = [
            [self.shoulder_center.idx, self.shoulder_center.rot],
            [self.hip_center.idx, self.hip_center.rot]
        ]
        for d in data:
            self.rotation_data.append(d)

    def shoulder_hip_location(self):
        """ Appending custom location data for driving the rig. """
        self.shoulder_center.loc = m_V.center_point(self.data[11][1], self.data[12][1])
        self.data.append([self.shoulder_center.idx, self.shoulder_center.loc])

        self.hip_center.loc = m_V.center_point(self.data[23][1], self.data[24][1])
        self.data.append([self.hip_center.idx, self.hip_center.loc])

    def prepare_landmarks(self):
        """ setting face mesh position to approximate origin """
        self.data = [[idx, np.array([-lmrk[0], lmrk[2], -lmrk[1]])] for idx, lmrk in self.data]
