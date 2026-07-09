import tensorflow as tf
import numpy as np
import operator

class Model:
    def __init__(self, model_path, labels, num_threads=1):
        self._interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=num_threads)
        self._interpreter.allocate_tensors()
        input_details = self._interpreter.get_input_details()
        output_details = self._interpreter.get_output_details()
        self._output_layer_index = output_details[0]["index"]
        self._input_layer_index = input_details[0]["index"]
        self.labels = labels
        #raise NotImplementedError

    def predict(self, samples):
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

        # Assign scores to labels - we use prediction[0] because we only have one batch entry
        p_labels = zip(range(len(self.labels)), self.labels, prediction[0])

        # Sort by score in ascending order
        p_sorted = sorted(p_labels, key=operator.itemgetter(2), reverse=True)

        # return top 5 predictions
        return list(p_sorted)[:5]


        #raise NotImplementedError

    @staticmethod
    def _flat_sigmoid(x, sensitivity=-1.0):
        return 1 / (1.0 + np.exp(sensitivity * np.clip(x, -15, 15)))




