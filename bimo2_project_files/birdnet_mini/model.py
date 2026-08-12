
"""
TensorFlow Lite model wrapper for bird species classification.

This module provides a lightweight wrapper around a TensorFlow Lite
BirdNET model. It handles model initialization, performs inference on
audio samples, and returns the highest-scoring predicted bird species.

The wrapper abstracts the low-level TensorFlow Lite interpreter interface
from the rest of the application.
"""

import tensorflow as tf
import numpy as np
import operator


class Model:
    """
    Wrapper around a TensorFlow Lite BirdNET model.

    The class loads a pretrained TensorFlow Lite model, performs
    inference on audio samples, and returns the highest-confidence
    predictions together with their labels.
    """

    def __init__(self, model_path, labels, num_threads=1):
        """
        Load and initialize the TensorFlow Lite model.

        Args:
            model_path: Path to the TensorFlow Lite model file.
            labels: List of class labels corresponding to the model outputs.
            num_threads: Number of CPU threads used during inference.
        """
        self._interpreter = tf.lite.Interpreter(
            model_path=model_path,
            num_threads=num_threads
        )
        self._interpreter.allocate_tensors()

        input_details = self._interpreter.get_input_details()
        output_details = self._interpreter.get_output_details()

        self._output_layer_index = output_details[0]["index"]
        self._input_layer_index = input_details[0]["index"]
        self.labels = labels

    def predict(self, samples):
        """
        Run inference on an audio sample.

        The input audio is converted to a float32 NumPy array and passed
        to the TensorFlow Lite interpreter. The resulting prediction
        scores are mapped to their corresponding labels, sorted by
        confidence, and the five most likely predictions are returned.

        Args:
            samples: Audio samples to classify.

        Returns:
            A list containing the five highest-scoring predictions.
            Each entry consists of the label index, label name, and
            confidence score.
        """
        # Convert samples to float32 numpy array
        input_data = np.array(samples, dtype=np.float32)

        # Set the input tensor
        self._interpreter.set_tensor(self._input_layer_index, [input_data])

        # Run inference
        self._interpreter.invoke()

        # Get the output tensor
        output_data = self._interpreter.get_tensor(self._output_layer_index)

        # Apply sigmoid function to the result
        prediction = self._flat_sigmoid(output_data)

        # Check if the prediction has the right shape
        assert prediction.shape[1] == len(self.labels)

        # Assign scores to labels - we use prediction[0] because
        # we only have one batch entry
        p_labels = zip(
            range(len(self.labels)),
            self.labels,
            prediction[0]
        )

        # Sort by score in descending order
        p_sorted = sorted(
            p_labels,
            key=operator.itemgetter(2),
            reverse=True
        )

        # Return top 5 predictions
        return list(p_sorted)[:5]

    @staticmethod
    def _flat_sigmoid(x, sensitivity=-1.0):
        """
        Apply a sigmoid activation function to model output values.

        Input values are clipped before applying the sigmoid function
        to reduce the risk of numerical overflow.

        Args:
            x: Model output values.
            sensitivity: Scaling factor applied to the input values.

        Returns:
            NumPy array containing sigmoid-transformed values in the
            range from 0 to 1.
        """
        return 1 / (1.0 + np.exp(sensitivity * np.clip(x, -15, 15)))
```
